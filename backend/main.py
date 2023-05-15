# This app is a backend which will push the data to kafka topic.
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel,validator
from fastapi.exceptions import HTTPException
from kafka import KafkaProducer, KafkaConsumer
import psycopg2 as pg
import io
import avro.io
import avro.schema
import uuid

app = FastAPI()

# database info
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "traffy"
DB_USER = "postgres"
DB_PASSWORD = "P@ssw0rd"



class InputText(BaseModel):
    text: str

    @validator('text')
    def check_text(cls, v):
        if len(v) == 0:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must not be empty"})
        if type(v) is not str:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must be string"})
        return v


class PredictedText(BaseModel):
    label: str
    text: str
    

class PredictedTexts(BaseModel):
    texts: list[PredictedText]

    @validator('texts')
    def check_texts(cls, v):
        if type(v) is not list:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must be list"})
        return v

def serialize(schema, obj):
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer = avro.io.DatumWriter(schema)
    writer.write(obj, encoder)
    return bytes_writer.getvalue() 

def deserialize(schema, raw_bytes):
    bytes_reader = io.BytesIO(raw_bytes)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    reader = avro.io.DatumReader(schema)
    return reader.read(decoder)

schema_file = 'traffy_input.avsc'
t_input_schema = avro.schema.parse(open(schema_file).read())
schema_file = 'traffy_output.avsc'
t_output_schema = avro.schema.parse(open(schema_file).read())

broker_url = 'localhost:9092'
# Create a Kafka producer
producer = KafkaProducer(
        bootstrap_servers=[broker_url],
        value_serializer=lambda x: serialize(t_input_schema, x)
    )

# Create a Kafka consumer
consumer = KafkaConsumer(
    'traffy-output',
    bootstrap_servers=[broker_url],
    value_deserializer= lambda x: deserialize(t_output_schema, x)
)



# add data to db
def add_data(tid, text, label):
    conn = pg.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute("INSERT INTO problems (id,text, label) VALUES (%s,%s, %s)", (tid ,text, label))
    conn.commit()
    cur.close()
    conn.close()

# Create web socket connection

# WebSocket endpoint
@app.websocket("/traffy")
async def broadcast(message: PredictedText):
    for websocket in app.state.websockets:
        try:
            await websocket.send_text(message)
        except:
            app.state.websockets.remove(websocket)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictedText)
async def predictFromStr(input_text: InputText):
    tid = str(uuid.uuid4())
    text = input_text.text
    # push the data to kafka topic
    producer.send('traffy-input', value={'tid': tid, 'text': text})
    # consume the data from kafka topic
    for msg in consumer:
        if msg.value['tid'] == tid:
            predicted = msg.value
            break
    print(predicted)

    await broadcast(predicted)

    
    # add data to db
    add_data(tid,predicted['text'], predicted['label'])
    return PredictedText(text=predicted['text'], label=predicted['label'])

@app.get("/predicts", response_model=PredictedTexts)
def predictFromList():
    # get data from db
    conn = pg.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute("SELECT * FROM problems")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print(rows)
    return PredictedTexts(texts=[PredictedText(text=row[1], label=row[2]) for row in rows])



    
@app.on_event("startup")
async def startup():
    app.state.websockets = set()

@app.on_event("shutdown")
async def shutdown():
    for websocket in app.state.websockets:
        await websocket.close()
