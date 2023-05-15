from kafka import KafkaConsumer
import json
import avro.schema
import avro.io
import io
# Define Kafka broker connection properties
broker_url = 'localhost:9092'
topic_name = 'traffy_input'
schema_file = 'traffy_input.avsc'
t_output_schema = avro.schema.parse(open(schema_file).read())

def deserialize(schema, raw_bytes):
    bytes_reader = io.BytesIO(raw_bytes)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    reader = avro.io.DatumReader(schema)
    return reader.read(decoder)

# Create Kafka consumer instance
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=[broker_url],
    value_deserializer=lambda x: deserialize(t_output_schema, x)
)

# Consume messages from Kafka
for message in consumer:
    print('Received message: {}'.format(  message.value))

# Close the Kafka consumer connection
consumer.close()
