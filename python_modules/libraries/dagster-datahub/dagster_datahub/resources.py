from dagster import Array, Field, InitResourceContext, Map, Noneable, Shape, StringSource, resource
from datahub.emitter.kafka_emitter import (
    DEFAULT_MCE_KAFKA_TOPIC,
    DEFAULT_MCP_KAFKA_TOPIC,
    MCE_KEY,
    MCP_KEY,
    DatahubKafkaEmitter,
    KafkaEmitterConfig,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter


@resource(
    config_schema={
        "connection": Field(StringSource, is_required=True, description="Datahub GMS Server"),
        "token": Field(
            Noneable(StringSource),
            default_value=None,
            is_required=False,
            description="Personal Access Token",
        ),
        "connect_timeout_sec": Field(Noneable(float), default_value=None, is_required=False),
        "read_timeout_sec": Field(Noneable(float), default_value=None, is_required=False),
        "retry_status_codes": Field(Noneable(Array(int)), default_value=None, is_required=False),
        "retry_methods": Field(Noneable(Array(str)), default_value=None, is_required=False),
        "retry_max_times": Field(Noneable(int), default_value=None, is_required=False),
        "extra_headers": Field(Noneable(Map(str, str)), default_value=None, is_required=False),
        "ca_certificate_path": Field(Noneable(str), default_value=None, is_required=False),
        "server_telemetry_id": Field(Noneable(str), default_value=None, is_required=False),
        "disable_ssl_verification": Field(bool, default_value=False, is_required=False),
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
                    is_required=True,
                    description="Kafka Boostrap Servers. Comma delimited",
                ),
                "schema_registry_url": Field(
                    StringSource,
                    is_required=True,
                    description="Schema Registry Location.",
                ),
                "schema_registry_config": Field(
                    dict,
                    default_value={},
                    is_required=False,
                    description="Extra Schema Registry Config.",
                ),
            }
        ),
        "topic": Field(str, default_value=DEFAULT_MCE_KAFKA_TOPIC, is_required=False),
        "topic_routes": Field(
            Map(str, str),
            default_value={
                MCE_KEY: DEFAULT_MCE_KAFKA_TOPIC,
                MCP_KEY: DEFAULT_MCP_KAFKA_TOPIC,
            },
            is_required=False,
        ),
    }
)
def datahub_kafka_emitter(init_context: InitResourceContext) -> DatahubKafkaEmitter:
    return DatahubKafkaEmitter(KafkaEmitterConfig.parse_obj(init_context.resource_config))
