# This app is a model to be consume kafka message and predict the label of the message.
# Then it will send the predicted label to kafka topic.
from model.model import predict
from kafka import KafkaConsumer, KafkaProducer
import io
import avro.io
import avro.schema

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

def main():
    schema_file = 'traffy_input.avsc'
    t_input_schema = avro.schema.parse(open(schema_file).read())
    schema_file = 'traffy_output.avsc'
    t_output_schema = avro.schema.parse(open(schema_file).read())


    consumer = KafkaConsumer(
        'traffy_input',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer= lambda x: deserialize(t_input_schema, x)
    )
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: serialize(t_output_schema, x)
    )

    for message in consumer:
        t_input = message.value
        predicted = predict([t_input['message']])
        t_output = {'tid': t_input['tid'], 'message':t_input['message'], 'label': predicted[1]}
        producer.send('traffy_output', t_output)


if __name__ == '__main__':
    main()