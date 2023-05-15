from kafka import KafkaConsumer
import json
# Define Kafka broker connection properties
broker_url = 'localhost:9092'
topic_name = 'traffy'

# Create Kafka consumer instance
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[broker_url],
    value_deserializer=lambda value: json.loads(value.decode('utf-8'))
)

# Consume messages from Kafka
for message in consumer:
    print('Received message: {}'.format(  message.value))

# Close the Kafka consumer connection
consumer.close()
