from typing import Any, Optional

from dagster import InitResourceContext, resource
from dagster._config.pythonic_config import Config, ConfigurableResource
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from datahub.emitter.kafka_emitter import (
    DEFAULT_MCE_KAFKA_TOPIC,
    DEFAULT_MCP_KAFKA_TOPIC,
    MCE_KEY,
    MCP_KEY,
    DatahubKafkaEmitter,
    KafkaEmitterConfig,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter
from pydantic import Field


class DatahubRESTEmitterResource(ConfigurableResource):
    connection: str = Field(description="Datahub GMS Server")
    token: Optional[str] = Field(default=None, description="Personal Access Token")
    connect_timeout_sec: Optional[float] = None
    read_timeout_sec: Optional[float] = None
    retry_status_codes: Optional[list[int]] = None
    retry_methods: Optional[list[str]] = None
    retry_max_times: Optional[int] = None
    extra_headers: Optional[dict[str, str]] = None
    ca_certificate_path: Optional[str] = None
    server_telemetry_id: Optional[str] = None  # No-op - no longer accepted in DatahubRestEmitter
    disable_ssl_verification: bool = False

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_emitter(self) -> DatahubRestEmitter:
        return DatahubRestEmitter(
            gms_server=self.connection,
            token=self.token,
            connect_timeout_sec=self.connect_timeout_sec,
            read_timeout_sec=self.read_timeout_sec,
            retry_status_codes=self.retry_status_codes,
            retry_methods=self.retry_methods,
            retry_max_times=self.retry_max_times,
            extra_headers=self.extra_headers,
            ca_certificate_path=self.ca_certificate_path,
            disable_ssl_verification=self.disable_ssl_verification,
        )


@dagster_maintained_resource
@resource(config_schema=DatahubRESTEmitterResource.to_config_schema())
def datahub_rest_emitter(init_context: InitResourceContext) -> DatahubRestEmitter:
    emitter = DatahubRestEmitter(
        gms_server=init_context.resource_config.get("connection"),
        token=init_context.resource_config.get("token"),
        connect_timeout_sec=init_context.resource_config.get("connect_timeout_sec"),
        read_timeout_sec=init_context.resource_config.get("read_timeout_sec"),
        retry_status_codes=init_context.resource_config.get("retry_status_codes"),
        retry_methods=init_context.resource_config.get("retry_methods"),
        retry_max_times=init_context.resource_config.get("retry_max_times"),
        extra_headers=init_context.resource_config.get("extra_headers"),
        ca_certificate_path=init_context.resource_config.get("ca_certificate_path"),
        disable_ssl_verification=init_context.resource_config.get("disable_ssl_verification"),
    )
    # Attempt to hit the server to ensure the resource is properly configured
    emitter.test_connection()
    return emitter


class DatahubConnection(Config):
    bootstrap: str = Field(description="Kafka Boostrap Servers. Comma delimited")
    schema_registry_url: str = Field(description="Schema Registry Location.")
    schema_registry_config: dict[str, Any] = Field(
        default={}, description="Extra Schema Registry Config."
    )


class DatahubKafkaEmitterResource(ConfigurableResource):
    connection: DatahubConnection
    topic_routes: dict[str, str] = Field(
        default={
            MCE_KEY: DEFAULT_MCE_KAFKA_TOPIC,
            MCP_KEY: DEFAULT_MCP_KAFKA_TOPIC,
        }
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def get_emitter(self) -> DatahubKafkaEmitter:
        return DatahubKafkaEmitter(
            KafkaEmitterConfig.parse_obj(
                {k: v for k, v in self._convert_to_config_dictionary().items() if v is not None}
            )
        )


@dagster_maintained_resource
@resource(config_schema=DatahubKafkaEmitterResource.to_config_schema())
def datahub_kafka_emitter(init_context: InitResourceContext) -> DatahubKafkaEmitter:
    return DatahubKafkaEmitter(KafkaEmitterConfig.parse_obj(init_context.resource_config))
