# This app is a backend which will push the data to kafka topic.
from fastapi import FastAPI
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

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictedText)
def predictFromList(input_text: InputText):
    tid = uuid.uuid4()
    text = input_text.text
    # push the data to kafka topic
    producer.send('traffy-input', value={'tid': str(tid), 'text': text})
    # consume the data from kafka topic
    for msg in consumer:
        if msg.value['tid'] == str(tid):
            predicted = msg.value
            break
    print(predicted)
    return PredictedText(text=predicted['text'], label=predicted['label'])
    
