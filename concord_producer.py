# !/usr/bin/env python
# python3 concord_producer_new.py --env dev --file_name calm_372_add.json


import json
import uuid
from argparse import ArgumentParser

from confluent_kafka import SerializingProducer
from confluent_kafka.error import ProduceError
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

SCHEMA_REGISTRY_URL = 'SCHEMA_REGISTRY_URL'
BOOTSTRAP_SERVERS = 'BOOTSTRAP_SERVERS'
SCHEMA_ID = 'SCHEMA_ID'

config = {
    'DEV': {
        'SCHEMA_REGISTRY_URL': 'http://10.41.43.221:8081',
        'BOOTSTRAP_SERVERS': '10.41.43.221:9092',
        'SCHEMA_ID': 1
    },
    'PROD': {
        'SCHEMA_REGISTRY_URL': 'http://10.41.43.222:8081',
        'BOOTSTRAP_SERVERS': '10.41.43.222:9092',
        'SCHEMA_ID': 20
    }
}
# software-metadata
TOPIC_NAME = 'testSoftwareMetaData'


def parse_command_line_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--env", required=False, help="environment in which script is running")
    arg_parser.add_argument("--file_name", required=False, help="File from which data will be pushed.")

    arg_parser.add_argument("--show_schema", required=False, const="store_const", nargs='?',
                            help="This argument is used to show the schema string for given schema id.")

    return arg_parser.parse_args()


def subject_strategy(ctx, val):
    return TOPIC_NAME + "-" + val


def load_file(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data


def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        print("Message is delivered...")


def create_producer(schema_id):
    schema_registry_client = get_schema_registry_client()
    schema_str = get_schema(schema_id, schema_registry_client)

    conf = {'subject.name.strategy': subject_strategy}
    value_serializer = AvroSerializer(schema_registry_client=schema_registry_client, schema_str=schema_str, conf=conf)

    producer_config = {
        "bootstrap.servers": config[env][BOOTSTRAP_SERVERS],
        "value.serializer": value_serializer
    }
    producer = SerializingProducer(producer_config)
    return producer


def send_record(schema_id):
    data_list = load_file(args.file_name)

    if not isinstance(data_list, list):
        raise Exception('File data is not list type.')
    elif len(data_list) == 0:
        raise Exception('File data is empty list.')

    print('Producing the record...')
    producer = create_producer(schema_id)

    for data in data_list:
        key = str(uuid.uuid4())

        try:
            producer.produce(topic=TOPIC_NAME, key=key, value=data, on_delivery=acked)
        except ProduceError as pe:
            print(f"Kafka produce error while producing record value - {data} to topic - {TOPIC_NAME}: {pe.kafka_message}")
        except Exception as e:
            print(f"Exception while producing record value - {data} to topic - {TOPIC_NAME}: {e}")
        else:
            print(f"Successfully producing record value - {data} to topic - {TOPIC_NAME}")

        producer.flush()


def get_schema(schema_id, schema_registry_client):
    schema_str = schema_registry_client.get_schema(schema_id=schema_id).schema_str
    return schema_str


def get_schema_registry_client():
    schema_registry_conf = {'url': config[env][SCHEMA_REGISTRY_URL]}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    return schema_registry_client


if __name__ == "__main__":
    args = parse_command_line_args()
    env = 'PROD' if args.env == 'prod' else 'DEV'

    if args.show_schema and args.file_name:
        raise Exception('Both argument "file_name" and "show_schema" is not allowed.')
    elif args.show_schema:
        schema_str = get_schema(config[env][SCHEMA_ID], get_schema_registry_client())
        print(f"Schema string value :- {schema_str}")
    elif args.file_name:
        send_record(config[env][SCHEMA_ID])
    else:
        raise Exception('Atleast one argument is needed from "file_name" or "show_schema"')
