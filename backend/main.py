# This app is a backend which will push the data to kafka topic.
from fastapi import FastAPI, WebSocket, Request
from pydantic import BaseModel,validator
from fastapi.exceptions import HTTPException
from kafka import KafkaProducer, KafkaConsumer
from fastapi.middleware.cors import CORSMiddleware
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
    success: bool = True
    label: str = ''
    text: str
    

class PredictedTexts(BaseModel):
    success: bool = True
    texts: list[str]

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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app.state.websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print("recieve #################",data)
            await broadcast(data)
    except:
        app.state.websockets.remove(websocket)

async def broadcast(message: dict):
    print("broadcasting", message)
    for websocket in app.state.websockets:
        try:
            print("Broadcasting ",message)
            await websocket.send_json(message)
        except:
            app.state.websockets.remove(websocket)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictedText)
async def predictFromStr(input_text: InputText):
    print(input_text)
    tid = str(uuid.uuid4())
    text = input_text.text



    # set time out for producer
    # push the data to kafka topic
    producer.send('traffy-input', value={'tid': tid, 'text': text})
    producer.flush()
    # set time out for consumer
    consumer.poll(timeout_ms=30000)
    consumer.seek_to_beginning()
    # consume the data from kafka topic
    for msg in consumer:
        if msg.value['tid'] == tid:
            predicted = msg.value
            break
    print(predicted)
    # return if consumer time out
    if predicted['label'] == '':

        return PredictedText(sucess=False,text='request time out', label='') 
    # add data to db
    add_data(tid,predicted['text'], predicted['label'])
    return PredictedText(text=predicted['text'], label=predicted['label'])

@app.get("/predicts", response_model=PredictedTexts)
def predictFromList():
    # get data from db
    conn = pg.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute("SELECT * FROM problems ")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    print(rows)
    rows.reverse()
    # return only text + : +  label

    return PredictedTexts(texts=[row[1] + "  :  " + row[2] for row in rows])



    
@app.on_event("startup")
async def startup():
    app.state.websockets = set()

@app.on_event("shutdown")
async def shutdown():
    for websocket in app.state.websockets:
        await websocket.close()


# allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


