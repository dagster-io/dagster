import pika
from dagster import resource

@resource(config_schema={"host": str})
def rabbitmq_connection_resource(init_context) -> pika.BlockingConnection:
    host = init_context.resource_config["host"]
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    yield connection
    connection.close()
