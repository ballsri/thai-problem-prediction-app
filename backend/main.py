# This app is a backend which will push the data to kafka topic.
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from pydantic import BaseModel,validator
from fastapi.exceptions import HTTPException
from kafka import KafkaProducer, KafkaConsumer
from fastapi.middleware.cors import CORSMiddleware
import psycopg2 as pg
import io
import avro.io
import avro.schema
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


app = FastAPI()

# database info
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "traffy"
DB_USER = "postgres"
DB_PASSWORD = "P@ssw0rd"



class InputText(BaseModel):
    tid: str
    text: str

    @validator('tid')
    def check_tid(cls, v):
        if len(v) == 0:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"tid must not be empty"})
        if type(v) is not str:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"tid must be string"})
        try:
        # Attempt to parse the UUID string
            uuid_obj = uuid.UUID(v)
            return v
        except ValueError:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"tid must be uuid"})
      


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
    value_deserializer= lambda x: deserialize(t_output_schema, x),
    group_id='1'
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

websocket_clients = []
# WebSocket endpoint
@app.websocket("/traffy")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print("recieve #################",data)
            await broadcast(data)
    except:
        websocket_clients.remove(websocket)

async def broadcast(message: dict):
    print("broadcasting", message)
    for websocket in websocket_clients:
        try:
            print("Broadcasting ",message)
            await websocket.send_json(message)
        except:
            websocket_clients.remove(websocket)

async def sendToPredict(tid, text):
    # set time out for producer
    # push the data to kafka topic
    producer.send('traffy-input', value={'tid': tid, 'text': text})
    producer.flush()
    # set time out for consumer
    consumer.poll(timeout_ms=3000)
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
    data = PredictedText(text=predicted['text'], label=predicted['label'])
    await broadcast( {"success" : True, "tid": tid,"result": data.text + "  :  " + data.label})

    return data

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict")
async def predictFromStr(input_text: InputText, background_tasks: BackgroundTasks):
    print(input_text)
    tid = input_text.tid
    text = input_text.text

    background_tasks.add_task(sendToPredict,tid, text)

    return {"success": True, "message" : "request is being processed"}

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



# create cron job to sent request to web 
# then get the response's data and sent to kafka topic
# then get the response from kafka topic and add to db
# then sent the response to web socket
# Run every 1 minute



