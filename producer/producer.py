# This file going to produce data, which are the response from api to Fondue web, to kafka topic

import json
import time
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime
import pandas as pd

# Kafka producer
broker_url = 'localhost:9092'
producer = KafkaProducer(bootstrap_servers=[broker_url],
                        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
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
    time.sleep(20)
    query_params['offset'] = str(offset)
    response = requests.get(url, params=query_params)
    data = response.json()
    df = pd.read_json(json.dumps(data['results']))
    df.drop(['type', 'org', 'coords', 'photo_url',
            'after_photo', 'address', 'timestamp', 'problem_type_abdul', 'star',
            'count_reopen', 'note', 'state', 'last_activity'], axis=1, inplace=True)
    for j in range(len(df)):
        producer.send('traffy', value=df.values[j].tolist())
        print(df.values[j].tolist())


    producer.flush()
    offset += 10