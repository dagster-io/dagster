from datahub.emitter.kafka_emitter import (
    DEFAULT_MCE_KAFKA_TOPIC,
    DEFAULT_MCP_KAFKA_TOPIC,
    MCE_KEY,
    MCP_KEY,
    DatahubKafkaEmitter,
    KafkaEmitterConfig,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter

from dagster import Array, Field, InitResourceContext, Map, Noneable, Shape, StringSource, resource


@resource(
    config_schema={
        "connection": Field(
            str, description="Datahub GMS Server", default_value="http://localhost:8080"
        ),
        "token": Field(Noneable(str), default_value=None, description="Personal Access Token"),
        "connect_timeout_sec": Field(Noneable(float), default_value=None),
        "read_timeout_sec": Field(Noneable(float), default_value=None),
        "retry_status_codes": Field(Noneable(Array(int)), default_value=None),
        "retry_methods": Field(Noneable(Array(str)), default_value=None),
        "retry_max_times": Field(Noneable(int), default_value=None),
        "extra_headers": Field(Noneable(Map(str, str)), default_value=None),
        "ca_certificate_path": Field(Noneable(str), default_value=None),
        "server_telemetry_id": Field(Noneable(str), default_value=None),
        "disable_ssl_verification": Field(bool, default_value=False),
    }
)
def datahub_rest_emitter(init_context: InitResourceContext) -> DatahubRestEmitter:
    emitter = DatahubRestEmitter(
        gms_server=init_context.resource_config["connection"],
        token=init_context.resource_config["token"],
        connect_timeout_sec=init_context.resource_config["connect_timeout_sec"],
        read_timeout_sec=init_context.resource_config["read_timeout_sec"],
        retry_status_codes=init_context.resource_config["retry_status_codes"],
        retry_methods=init_context.resource_config["retry_methods"],
        retry_max_times=init_context.resource_config["retry_max_times"],
        extra_headers=init_context.resource_config["extra_headers"],
        ca_certificate_path=init_context.resource_config["ca_certificate_path"],
        server_telemetry_id=init_context.resource_config["server_telemetry_id"],
        disable_ssl_verification=init_context.resource_config["disable_ssl_verification"],
    )
    # Attempt to hit the server to ensure the resource is properly configured
    emitter.test_connection()
    return emitter


@resource(
    config_schema={
        "connection": Shape(
            {
                "bootstrap": Field(
                    StringSource,
                    description="Kafka Boostrap Servers. Comma delimited",
                ),
                "schema_registry_url": Field(
                    str,
                    default_value="http://localhost:8081",
                    description="Schema Registry Location.",
                ),
                "schema_registry_config": Field(
                    dict, default_value={}, description="Extra Schema Registry Config."
                ),
            }
        ),
        "topic": Field(str, default_value=DEFAULT_MCE_KAFKA_TOPIC),
        "topic_routes": Field(
            Map(str, str),
            default_value={
                MCE_KEY: DEFAULT_MCE_KAFKA_TOPIC,
                MCP_KEY: DEFAULT_MCP_KAFKA_TOPIC,
            },
        ),
    }
)
def datahub_kafka_emitter(init_context: InitResourceContext) -> DatahubKafkaEmitter:
    return DatahubKafkaEmitter(KafkaEmitterConfig.parse_obj(init_context.resource_config))
