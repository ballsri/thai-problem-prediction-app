# This file going to produce data, which are the response from api to Fondue web, to kafka topic

import json
import time
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime
import pandas as pd
import avro.schema
import avro.io
import io

# Kafka producer


schema_file = 'traffy_input.avsc'
t_input_schema = avro.schema.parse(open(schema_file).read())

def serialize(schema, obj):
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer = avro.io.DatumWriter(schema)
    writer.write(obj, encoder)
    return bytes_writer.getvalue()


broker_url = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=[broker_url],
                        value_serializer=lambda x: serialize(t_input_schema, x)
    )

# API url
offset = 0
url = 'https://publicapi.traffy.in.th/share/teamchadchart/search'
query_params = {
    'limit': "10",
    'sort': "ASC",
    'offset': str(offset)
}

# produce data to kafka topic
while True:
    query_params['offset'] = str(offset)
    response = requests.get(url, params=query_params)
    data = response.json()
    df = pd.read_json(json.dumps(data['results']))
    df.drop(['type', 'org', 'coords', 'photo_url',
            'after_photo', 'address', 'timestamp', 'problem_type_abdul', 'star',
            'count_reopen', 'note', 'state', 'last_activity'], axis=1, inplace=True)
    for j in range(len(df)):
        producer.send('traffy_input', value={"tid": df.values[j].tolist()[1], "message": df.values[j].tolist()[0]})
        print(df.values[j].tolist())


    producer.flush()
    offset += 10
    time.sleep(20)