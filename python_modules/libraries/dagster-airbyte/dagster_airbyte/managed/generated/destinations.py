# pylint: disable=unused-import,redefined-builtin
from typing import Any, List, Optional, Union

from dagster_airbyte.managed.types import GeneratedAirbyteDestination

import dagster._check as check


class DynamodbDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        dynamodb_table_name_prefix: str,
        dynamodb_region: str,
        access_key_id: str,
        secret_access_key: str,
        dynamodb_endpoint: Optional[str] = None,
    ):
        """
        Airbyte Destination for Dynamodb

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/dynamodb
        """
        self.dynamodb_endpoint = check.opt_str_param(dynamodb_endpoint, "dynamodb_endpoint")
        self.dynamodb_table_name_prefix = check.str_param(
            dynamodb_table_name_prefix, "dynamodb_table_name_prefix"
        )
        self.dynamodb_region = check.str_param(dynamodb_region, "dynamodb_region")
        self.access_key_id = check.str_param(access_key_id, "access_key_id")
        self.secret_access_key = check.str_param(secret_access_key, "secret_access_key")
        super().__init__("Dynamodb", name)


class BigqueryDestination(GeneratedAirbyteDestination):
    class StandardInserts:
        def __init__(
            self,
        ):
            self.method = "Standard"

    class HMACKey:
        def __init__(self, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = "HMAC_KEY"
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class GCSStaging:
        def __init__(
            self,
            credential: "BigqueryDestination.HMACKey",
            gcs_bucket_name: str,
            gcs_bucket_path: str,
            keep_files_in_gcs_bucket: Optional[str] = None,
        ):
            self.method = "GCS Staging"
            self.credential = check.inst_param(
                credential, "credential", BigqueryDestination.HMACKey
            )
            self.gcs_bucket_name = check.str_param(gcs_bucket_name, "gcs_bucket_name")
            self.gcs_bucket_path = check.str_param(gcs_bucket_path, "gcs_bucket_path")
            self.keep_files_in_gcs_bucket = check.opt_str_param(
                keep_files_in_gcs_bucket, "keep_files_in_gcs_bucket"
            )

    def __init__(
        self,
        name: str,
        project_id: str,
        dataset_location: str,
        dataset_id: str,
        loading_method: Union[StandardInserts, GCSStaging],
        credentials_json: Optional[str] = None,
        transformation_priority: Optional[str] = None,
        big_query_client_buffer_size_mb: Optional[int] = None,
    ):
        """
        Airbyte Destination for Bigquery

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/bigquery
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.dataset_location = check.str_param(dataset_location, "dataset_location")
        self.dataset_id = check.str_param(dataset_id, "dataset_id")
        self.loading_method = check.inst_param(
            loading_method,
            "loading_method",
            (BigqueryDestination.StandardInserts, BigqueryDestination.GCSStaging),
        )
        self.credentials_json = check.opt_str_param(credentials_json, "credentials_json")
        self.transformation_priority = check.opt_str_param(
            transformation_priority, "transformation_priority"
        )
        self.big_query_client_buffer_size_mb = check.opt_int_param(
            big_query_client_buffer_size_mb, "big_query_client_buffer_size_mb"
        )
        super().__init__("Bigquery", name)


class RabbitmqDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        routing_key: str,
        ssl: Optional[bool] = None,
        port: Optional[int] = None,
        virtual_host: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        exchange: Optional[str] = None,
    ):
        """
        Airbyte Destination for Rabbitmq

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/rabbitmq
        """
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.host = check.str_param(host, "host")
        self.port = check.opt_int_param(port, "port")
        self.virtual_host = check.opt_str_param(virtual_host, "virtual_host")
        self.username = check.opt_str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.exchange = check.opt_str_param(exchange, "exchange")
        self.routing_key = check.str_param(routing_key, "routing_key")
        super().__init__("Rabbitmq", name)


class KvdbDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, bucket_id: str, secret_key: str):
        """
        Airbyte Destination for Kvdb

        Documentation can be found at https://kvdb.io/docs/api/
        """
        self.bucket_id = check.str_param(bucket_id, "bucket_id")
        self.secret_key = check.str_param(secret_key, "secret_key")
        super().__init__("Kvdb", name)


class ClickhouseDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        ssl: Optional[bool] = None,
    ):
        """
        Airbyte Destination for Clickhouse

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/clickhouse
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        super().__init__("Clickhouse", name)


class AmazonSqsDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        queue_url: str,
        region: str,
        message_delay: Optional[int] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        message_body_key: Optional[str] = None,
        message_group_id: Optional[str] = None,
    ):
        """
        Airbyte Destination for Amazon Sqs

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/amazon-sqs
        """
        self.queue_url = check.str_param(queue_url, "queue_url")
        self.region = check.str_param(region, "region")
        self.message_delay = check.opt_int_param(message_delay, "message_delay")
        self.access_key = check.opt_str_param(access_key, "access_key")
        self.secret_key = check.opt_str_param(secret_key, "secret_key")
        self.message_body_key = check.opt_str_param(message_body_key, "message_body_key")
        self.message_group_id = check.opt_str_param(message_group_id, "message_group_id")
        super().__init__("Amazon Sqs", name)


class MariadbColumnstoreDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Mariadb Columnstore

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mariadb-columnstore
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Mariadb Columnstore", name)


class KinesisDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        endpoint: str,
        region: str,
        shardCount: int,
        accessKey: str,
        privateKey: str,
        bufferSize: int,
    ):
        """
        Airbyte Destination for Kinesis

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/kinesis
        """
        self.endpoint = check.str_param(endpoint, "endpoint")
        self.region = check.str_param(region, "region")
        self.shardCount = check.int_param(shardCount, "shardCount")
        self.accessKey = check.str_param(accessKey, "accessKey")
        self.privateKey = check.str_param(privateKey, "privateKey")
        self.bufferSize = check.int_param(bufferSize, "bufferSize")
        super().__init__("Kinesis", name)


class AzureBlobStorageDestination(GeneratedAirbyteDestination):
    class CSVCommaSeparatedValues:
        def __init__(self, flattening: str):
            self.format_type = "CSV"
            self.flattening = check.str_param(flattening, "flattening")

    class JSONLinesNewlineDelimitedJSON:
        def __init__(
            self,
        ):
            self.format_type = "JSONL"

    def __init__(
        self,
        name: str,
        azure_blob_storage_account_name: str,
        azure_blob_storage_account_key: str,
        format: Union[CSVCommaSeparatedValues, JSONLinesNewlineDelimitedJSON],
        azure_blob_storage_endpoint_domain_name: Optional[str] = None,
        azure_blob_storage_container_name: Optional[str] = None,
        azure_blob_storage_output_buffer_size: Optional[int] = None,
    ):
        """
        Airbyte Destination for Azure Blob Storage

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/azureblobstorage
        """
        self.azure_blob_storage_endpoint_domain_name = check.opt_str_param(
            azure_blob_storage_endpoint_domain_name, "azure_blob_storage_endpoint_domain_name"
        )
        self.azure_blob_storage_container_name = check.opt_str_param(
            azure_blob_storage_container_name, "azure_blob_storage_container_name"
        )
        self.azure_blob_storage_account_name = check.str_param(
            azure_blob_storage_account_name, "azure_blob_storage_account_name"
        )
        self.azure_blob_storage_account_key = check.str_param(
            azure_blob_storage_account_key, "azure_blob_storage_account_key"
        )
        self.azure_blob_storage_output_buffer_size = check.opt_int_param(
            azure_blob_storage_output_buffer_size, "azure_blob_storage_output_buffer_size"
        )
        self.format = check.inst_param(
            format,
            "format",
            (
                AzureBlobStorageDestination.CSVCommaSeparatedValues,
                AzureBlobStorageDestination.JSONLinesNewlineDelimitedJSON,
            ),
        )
        super().__init__("Azure Blob Storage", name)


class KafkaDestination(GeneratedAirbyteDestination):
    class PLAINTEXT:
        def __init__(self, security_protocol: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")

    class SASLPLAINTEXT:
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    class SASLSSL:
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    def __init__(
        self,
        name: str,
        bootstrap_servers: str,
        topic_pattern: str,
        protocol: Union[PLAINTEXT, SASLPLAINTEXT, SASLSSL],
        acks: str,
        enable_idempotence: bool,
        compression_type: str,
        batch_size: int,
        linger_ms: str,
        max_in_flight_requests_per_connection: int,
        client_dns_lookup: str,
        buffer_memory: str,
        max_request_size: int,
        retries: int,
        socket_connection_setup_timeout_ms: str,
        socket_connection_setup_timeout_max_ms: str,
        max_block_ms: str,
        request_timeout_ms: int,
        delivery_timeout_ms: int,
        send_buffer_bytes: int,
        receive_buffer_bytes: int,
        test_topic: Optional[str] = None,
        sync_producer: Optional[bool] = None,
        client_id: Optional[str] = None,
    ):
        """
        Airbyte Destination for Kafka

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/kafka
        """
        self.bootstrap_servers = check.str_param(bootstrap_servers, "bootstrap_servers")
        self.topic_pattern = check.str_param(topic_pattern, "topic_pattern")
        self.test_topic = check.opt_str_param(test_topic, "test_topic")
        self.sync_producer = check.opt_bool_param(sync_producer, "sync_producer")
        self.protocol = check.inst_param(
            protocol,
            "protocol",
            (KafkaDestination.PLAINTEXT, KafkaDestination.SASLPLAINTEXT, KafkaDestination.SASLSSL),
        )
        self.client_id = check.opt_str_param(client_id, "client_id")
        self.acks = check.str_param(acks, "acks")
        self.enable_idempotence = check.bool_param(enable_idempotence, "enable_idempotence")
        self.compression_type = check.str_param(compression_type, "compression_type")
        self.batch_size = check.int_param(batch_size, "batch_size")
        self.linger_ms = check.str_param(linger_ms, "linger_ms")
        self.max_in_flight_requests_per_connection = check.int_param(
            max_in_flight_requests_per_connection, "max_in_flight_requests_per_connection"
        )
        self.client_dns_lookup = check.str_param(client_dns_lookup, "client_dns_lookup")
        self.buffer_memory = check.str_param(buffer_memory, "buffer_memory")
        self.max_request_size = check.int_param(max_request_size, "max_request_size")
        self.retries = check.int_param(retries, "retries")
        self.socket_connection_setup_timeout_ms = check.str_param(
            socket_connection_setup_timeout_ms, "socket_connection_setup_timeout_ms"
        )
        self.socket_connection_setup_timeout_max_ms = check.str_param(
            socket_connection_setup_timeout_max_ms, "socket_connection_setup_timeout_max_ms"
        )
        self.max_block_ms = check.str_param(max_block_ms, "max_block_ms")
        self.request_timeout_ms = check.int_param(request_timeout_ms, "request_timeout_ms")
        self.delivery_timeout_ms = check.int_param(delivery_timeout_ms, "delivery_timeout_ms")
        self.send_buffer_bytes = check.int_param(send_buffer_bytes, "send_buffer_bytes")
        self.receive_buffer_bytes = check.int_param(receive_buffer_bytes, "receive_buffer_bytes")
        super().__init__("Kafka", name)


class ElasticsearchDestination(GeneratedAirbyteDestination):
    class None_:
        def __init__(
            self,
        ):
            self.method = "none"

    class ApiKeySecret:
        def __init__(self, apiKeyId: str, apiKeySecret: str):
            self.method = "secret"
            self.apiKeyId = check.str_param(apiKeyId, "apiKeyId")
            self.apiKeySecret = check.str_param(apiKeySecret, "apiKeySecret")

    class UsernamePassword:
        def __init__(self, username: str, password: str):
            self.method = "basic"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    def __init__(
        self,
        name: str,
        endpoint: str,
        authenticationMethod: Union[None_, ApiKeySecret, UsernamePassword],
        upsert: Optional[bool] = None,
    ):
        """
        Airbyte Destination for Elasticsearch

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/elasticsearch
        """
        self.endpoint = check.str_param(endpoint, "endpoint")
        self.upsert = check.opt_bool_param(upsert, "upsert")
        self.authenticationMethod = check.inst_param(
            authenticationMethod,
            "authenticationMethod",
            (
                ElasticsearchDestination.None_,
                ElasticsearchDestination.ApiKeySecret,
                ElasticsearchDestination.UsernamePassword,
            ),
        )
        super().__init__("Elasticsearch", name)


class MysqlDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        ssl: Optional[bool] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Mysql

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mysql
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Mysql", name)


class SftpJsonDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        username: str,
        password: str,
        destination_path: str,
        port: Optional[int] = None,
    ):
        """
        Airbyte Destination for Sftp Json

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/sftp-json
        """
        self.host = check.str_param(host, "host")
        self.port = check.opt_int_param(port, "port")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Sftp Json", name)


class GcsDestination(GeneratedAirbyteDestination):
    class HMACKey:
        def __init__(self, credential_type: str, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = check.str_param(credential_type, "credential_type")
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class NoCompression:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        def __init__(self, codec: str, compression_level: Optional[int] = None):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.opt_int_param(compression_level, "compression_level")

    class Bzip2:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        def __init__(self, codec: str, compression_level: Optional[int] = None):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.opt_int_param(compression_level, "compression_level")

    class Zstandard:
        def __init__(
            self,
            codec: str,
            compression_level: Optional[int] = None,
            include_checksum: Optional[bool] = None,
        ):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.opt_int_param(compression_level, "compression_level")
            self.include_checksum = check.opt_bool_param(include_checksum, "include_checksum")

    class Snappy:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        def __init__(
            self,
            format_type: str,
            compression_codec: Union[
                "GcsDestination.NoCompression",
                "GcsDestination.Deflate",
                "GcsDestination.Bzip2",
                "GcsDestination.Xz",
                "GcsDestination.Zstandard",
                "GcsDestination.Snappy",
            ],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression_codec = check.inst_param(
                compression_codec,
                "compression_codec",
                (
                    GcsDestination.NoCompression,
                    GcsDestination.Deflate,
                    GcsDestination.Bzip2,
                    GcsDestination.Xz,
                    GcsDestination.Zstandard,
                    GcsDestination.Snappy,
                ),
            )

    class GZIP:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        def __init__(
            self,
            format_type: str,
            compression: Union["GcsDestination.NoCompression", "GcsDestination.GZIP"],
            flattening: Optional[str] = None,
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.flattening = check.opt_str_param(flattening, "flattening")
            self.compression = check.inst_param(
                compression, "compression", (GcsDestination.NoCompression, GcsDestination.GZIP)
            )

    class JSONLinesNewlineDelimitedJSON:
        def __init__(
            self,
            format_type: str,
            compression: Union["GcsDestination.NoCompression", "GcsDestination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression = check.inst_param(
                compression, "compression", (GcsDestination.NoCompression, GcsDestination.GZIP)
            )

    class ParquetColumnarStorage:
        def __init__(
            self,
            format_type: str,
            compression_codec: Optional[str] = None,
            block_size_mb: Optional[int] = None,
            max_padding_size_mb: Optional[int] = None,
            page_size_kb: Optional[int] = None,
            dictionary_page_size_kb: Optional[int] = None,
            dictionary_encoding: Optional[bool] = None,
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression_codec = check.opt_str_param(compression_codec, "compression_codec")
            self.block_size_mb = check.opt_int_param(block_size_mb, "block_size_mb")
            self.max_padding_size_mb = check.opt_int_param(
                max_padding_size_mb, "max_padding_size_mb"
            )
            self.page_size_kb = check.opt_int_param(page_size_kb, "page_size_kb")
            self.dictionary_page_size_kb = check.opt_int_param(
                dictionary_page_size_kb, "dictionary_page_size_kb"
            )
            self.dictionary_encoding = check.opt_bool_param(
                dictionary_encoding, "dictionary_encoding"
            )

    def __init__(
        self,
        name: str,
        gcs_bucket_name: str,
        gcs_bucket_path: str,
        credential: HMACKey,
        format: Union[
            AvroApacheAvro,
            CSVCommaSeparatedValues,
            JSONLinesNewlineDelimitedJSON,
            ParquetColumnarStorage,
        ],
        gcs_bucket_region: Optional[str] = None,
    ):
        """
        Airbyte Destination for Gcs

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/gcs
        """
        self.gcs_bucket_name = check.str_param(gcs_bucket_name, "gcs_bucket_name")
        self.gcs_bucket_path = check.str_param(gcs_bucket_path, "gcs_bucket_path")
        self.gcs_bucket_region = check.opt_str_param(gcs_bucket_region, "gcs_bucket_region")
        self.credential = check.inst_param(credential, "credential", GcsDestination.HMACKey)
        self.format = check.inst_param(
            format,
            "format",
            (
                GcsDestination.AvroApacheAvro,
                GcsDestination.CSVCommaSeparatedValues,
                GcsDestination.JSONLinesNewlineDelimitedJSON,
                GcsDestination.ParquetColumnarStorage,
            ),
        )
        super().__init__("Gcs", name)


class CassandraDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        keyspace: str,
        username: str,
        password: str,
        address: str,
        port: int,
        datacenter: Optional[str] = None,
        replication: Optional[int] = None,
    ):
        """
        Airbyte Destination for Cassandra

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/cassandra
        """
        self.keyspace = check.str_param(keyspace, "keyspace")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.address = check.str_param(address, "address")
        self.port = check.int_param(port, "port")
        self.datacenter = check.opt_str_param(datacenter, "datacenter")
        self.replication = check.opt_int_param(replication, "replication")
        super().__init__("Cassandra", name)


class FireboltDestination(GeneratedAirbyteDestination):
    class SQLInserts:
        def __init__(
            self,
        ):
            self.method = "SQL"

    class ExternalTableViaS3:
        def __init__(self, s3_bucket: str, s3_region: str, aws_key_id: str, aws_key_secret: str):
            self.method = "S3"
            self.s3_bucket = check.str_param(s3_bucket, "s3_bucket")
            self.s3_region = check.str_param(s3_region, "s3_region")
            self.aws_key_id = check.str_param(aws_key_id, "aws_key_id")
            self.aws_key_secret = check.str_param(aws_key_secret, "aws_key_secret")

    def __init__(
        self,
        name: str,
        username: str,
        password: str,
        database: str,
        loading_method: Union[SQLInserts, ExternalTableViaS3],
        account: Optional[str] = None,
        host: Optional[str] = None,
        engine: Optional[str] = None,
    ):
        """
        Airbyte Destination for Firebolt

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/firebolt
        """
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.account = check.opt_str_param(account, "account")
        self.host = check.opt_str_param(host, "host")
        self.database = check.str_param(database, "database")
        self.engine = check.opt_str_param(engine, "engine")
        self.loading_method = check.inst_param(
            loading_method,
            "loading_method",
            (FireboltDestination.SQLInserts, FireboltDestination.ExternalTableViaS3),
        )
        super().__init__("Firebolt", name)


class GoogleSheetsDestination(GeneratedAirbyteDestination):
    class AuthenticationViaGoogleOAuth:
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    def __init__(self, name: str, spreadsheet_id: str, credentials: AuthenticationViaGoogleOAuth):
        """
        Airbyte Destination for Google Sheets

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/google-sheets
        """
        self.spreadsheet_id = check.str_param(spreadsheet_id, "spreadsheet_id")
        self.credentials = check.inst_param(
            credentials, "credentials", GoogleSheetsDestination.AuthenticationViaGoogleOAuth
        )
        super().__init__("Google Sheets", name)


class DatabricksDestination(GeneratedAirbyteDestination):
    class AmazonS3:
        def __init__(
            self,
            data_source_type: str,
            s3_bucket_name: str,
            s3_bucket_path: str,
            s3_bucket_region: str,
            s3_access_key_id: str,
            s3_secret_access_key: str,
            file_name_pattern: Optional[str] = None,
        ):
            self.data_source_type = check.str_param(data_source_type, "data_source_type")
            self.s3_bucket_name = check.str_param(s3_bucket_name, "s3_bucket_name")
            self.s3_bucket_path = check.str_param(s3_bucket_path, "s3_bucket_path")
            self.s3_bucket_region = check.str_param(s3_bucket_region, "s3_bucket_region")
            self.s3_access_key_id = check.str_param(s3_access_key_id, "s3_access_key_id")
            self.s3_secret_access_key = check.str_param(
                s3_secret_access_key, "s3_secret_access_key"
            )
            self.file_name_pattern = check.opt_str_param(file_name_pattern, "file_name_pattern")

    class AzureBlobStorage:
        def __init__(
            self,
            data_source_type: str,
            azure_blob_storage_account_name: str,
            azure_blob_storage_container_name: str,
            azure_blob_storage_sas_token: str,
            azure_blob_storage_endpoint_domain_name: Optional[str] = None,
        ):
            self.data_source_type = check.str_param(data_source_type, "data_source_type")
            self.azure_blob_storage_endpoint_domain_name = check.opt_str_param(
                azure_blob_storage_endpoint_domain_name, "azure_blob_storage_endpoint_domain_name"
            )
            self.azure_blob_storage_account_name = check.str_param(
                azure_blob_storage_account_name, "azure_blob_storage_account_name"
            )
            self.azure_blob_storage_container_name = check.str_param(
                azure_blob_storage_container_name, "azure_blob_storage_container_name"
            )
            self.azure_blob_storage_sas_token = check.str_param(
                azure_blob_storage_sas_token, "azure_blob_storage_sas_token"
            )

    def __init__(
        self,
        name: str,
        accept_terms: bool,
        databricks_server_hostname: str,
        databricks_http_path: str,
        databricks_personal_access_token: str,
        data_source: Union[AmazonS3, AzureBlobStorage],
        databricks_port: Optional[str] = None,
        database_schema: Optional[str] = None,
        purge_staging_data: Optional[bool] = None,
    ):
        """
        Airbyte Destination for Databricks

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/databricks
        """
        self.accept_terms = check.bool_param(accept_terms, "accept_terms")
        self.databricks_server_hostname = check.str_param(
            databricks_server_hostname, "databricks_server_hostname"
        )
        self.databricks_http_path = check.str_param(databricks_http_path, "databricks_http_path")
        self.databricks_port = check.opt_str_param(databricks_port, "databricks_port")
        self.databricks_personal_access_token = check.str_param(
            databricks_personal_access_token, "databricks_personal_access_token"
        )
        self.database_schema = check.opt_str_param(database_schema, "database_schema")
        self.data_source = check.inst_param(
            data_source,
            "data_source",
            (DatabricksDestination.AmazonS3, DatabricksDestination.AzureBlobStorage),
        )
        self.purge_staging_data = check.opt_bool_param(purge_staging_data, "purge_staging_data")
        super().__init__("Databricks", name)


class BigqueryDenormalizedDestination(GeneratedAirbyteDestination):
    class StandardInserts:
        def __init__(
            self,
        ):
            self.method = "Standard"

    class HMACKey:
        def __init__(self, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = "HMAC_KEY"
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class GCSStaging:
        def __init__(
            self,
            credential: "BigqueryDenormalizedDestination.HMACKey",
            gcs_bucket_name: str,
            gcs_bucket_path: str,
            keep_files_in_gcs_bucket: Optional[str] = None,
        ):
            self.method = "GCS Staging"
            self.credential = check.inst_param(
                credential, "credential", BigqueryDenormalizedDestination.HMACKey
            )
            self.gcs_bucket_name = check.str_param(gcs_bucket_name, "gcs_bucket_name")
            self.gcs_bucket_path = check.str_param(gcs_bucket_path, "gcs_bucket_path")
            self.keep_files_in_gcs_bucket = check.opt_str_param(
                keep_files_in_gcs_bucket, "keep_files_in_gcs_bucket"
            )

    def __init__(
        self,
        name: str,
        project_id: str,
        dataset_id: str,
        loading_method: Union[StandardInserts, GCSStaging],
        credentials_json: Optional[str] = None,
        dataset_location: Optional[str] = None,
        big_query_client_buffer_size_mb: Optional[int] = None,
    ):
        """
        Airbyte Destination for Bigquery Denormalized

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/bigquery
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.dataset_id = check.str_param(dataset_id, "dataset_id")
        self.loading_method = check.inst_param(
            loading_method,
            "loading_method",
            (
                BigqueryDenormalizedDestination.StandardInserts,
                BigqueryDenormalizedDestination.GCSStaging,
            ),
        )
        self.credentials_json = check.opt_str_param(credentials_json, "credentials_json")
        self.dataset_location = check.opt_str_param(dataset_location, "dataset_location")
        self.big_query_client_buffer_size_mb = check.opt_int_param(
            big_query_client_buffer_size_mb, "big_query_client_buffer_size_mb"
        )
        super().__init__("Bigquery Denormalized", name)


class SqliteDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, destination_path: str):
        """
        Airbyte Destination for Sqlite

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/sqlite
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Sqlite", name)


class MongodbDestination(GeneratedAirbyteDestination):
    class StandaloneMongoDbInstance:
        def __init__(self, instance: str, host: str, port: int, tls: Optional[bool] = None):
            self.instance = check.str_param(instance, "instance")
            self.host = check.str_param(host, "host")
            self.port = check.int_param(port, "port")
            self.tls = check.opt_bool_param(tls, "tls")

    class ReplicaSet:
        def __init__(self, instance: str, server_addresses: str, replica_set: Optional[str] = None):
            self.instance = check.str_param(instance, "instance")
            self.server_addresses = check.str_param(server_addresses, "server_addresses")
            self.replica_set = check.opt_str_param(replica_set, "replica_set")

    class MongoDBAtlas:
        def __init__(self, instance: str, cluster_url: str):
            self.instance = check.str_param(instance, "instance")
            self.cluster_url = check.str_param(cluster_url, "cluster_url")

    class None_:
        def __init__(
            self,
        ):
            self.authorization = "none"

    class LoginPassword:
        def __init__(self, username: str, password: str):
            self.authorization = "login/password"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    def __init__(
        self,
        name: str,
        instance_type: Union[StandaloneMongoDbInstance, ReplicaSet, MongoDBAtlas],
        database: str,
        auth_type: Union[None_, LoginPassword],
    ):
        """
        Airbyte Destination for Mongodb

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mongodb
        """
        self.instance_type = check.inst_param(
            instance_type,
            "instance_type",
            (
                MongodbDestination.StandaloneMongoDbInstance,
                MongodbDestination.ReplicaSet,
                MongodbDestination.MongoDBAtlas,
            ),
        )
        self.database = check.str_param(database, "database")
        self.auth_type = check.inst_param(
            auth_type, "auth_type", (MongodbDestination.None_, MongodbDestination.LoginPassword)
        )
        super().__init__("Mongodb", name)


class RocksetDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, api_key: str, workspace: str, api_server: Optional[str] = None):
        """
        Airbyte Destination for Rockset

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/rockset
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.workspace = check.str_param(workspace, "workspace")
        self.api_server = check.opt_str_param(api_server, "api_server")
        super().__init__("Rockset", name)


class OracleDestination(GeneratedAirbyteDestination):
    class Unencrypted:
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class NativeNetworkEncryptionNNE:
        def __init__(self, encryption_algorithm: Optional[str] = None):
            self.encryption_method = "client_nne"
            self.encryption_algorithm = check.opt_str_param(
                encryption_algorithm, "encryption_algorithm"
            )

    class TLSEncryptedVerifyCertificate:
        def __init__(self, ssl_certificate: str):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        sid: str,
        username: str,
        encryption: Union[Unencrypted, NativeNetworkEncryptionNNE, TLSEncryptedVerifyCertificate],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        """
        Airbyte Destination for Oracle

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/oracle
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.sid = check.str_param(sid, "sid")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.schema = check.opt_str_param(schema, "schema")
        self.encryption = check.inst_param(
            encryption,
            "encryption",
            (
                OracleDestination.Unencrypted,
                OracleDestination.NativeNetworkEncryptionNNE,
                OracleDestination.TLSEncryptedVerifyCertificate,
            ),
        )
        super().__init__("Oracle", name)


class CsvDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, destination_path: str):
        """
        Airbyte Destination for Csv

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/local-csv
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Csv", name)


class S3Destination(GeneratedAirbyteDestination):
    class NoCompression:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Bzip2:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Zstandard:
        def __init__(
            self, codec: str, compression_level: int, include_checksum: Optional[bool] = None
        ):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")
            self.include_checksum = check.opt_bool_param(include_checksum, "include_checksum")

    class Snappy:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        def __init__(
            self,
            format_type: str,
            compression_codec: Union[
                "S3Destination.NoCompression",
                "S3Destination.Deflate",
                "S3Destination.Bzip2",
                "S3Destination.Xz",
                "S3Destination.Zstandard",
                "S3Destination.Snappy",
            ],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression_codec = check.inst_param(
                compression_codec,
                "compression_codec",
                (
                    S3Destination.NoCompression,
                    S3Destination.Deflate,
                    S3Destination.Bzip2,
                    S3Destination.Xz,
                    S3Destination.Zstandard,
                    S3Destination.Snappy,
                ),
            )

    class GZIP:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        def __init__(
            self,
            format_type: str,
            flattening: str,
            compression: Union["S3Destination.NoCompression", "S3Destination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.flattening = check.str_param(flattening, "flattening")
            self.compression = check.inst_param(
                compression, "compression", (S3Destination.NoCompression, S3Destination.GZIP)
            )

    class JSONLinesNewlineDelimitedJSON:
        def __init__(
            self,
            format_type: str,
            compression: Union["S3Destination.NoCompression", "S3Destination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression = check.inst_param(
                compression, "compression", (S3Destination.NoCompression, S3Destination.GZIP)
            )

    class ParquetColumnarStorage:
        def __init__(
            self,
            format_type: str,
            compression_codec: Optional[str] = None,
            block_size_mb: Optional[int] = None,
            max_padding_size_mb: Optional[int] = None,
            page_size_kb: Optional[int] = None,
            dictionary_page_size_kb: Optional[int] = None,
            dictionary_encoding: Optional[bool] = None,
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression_codec = check.opt_str_param(compression_codec, "compression_codec")
            self.block_size_mb = check.opt_int_param(block_size_mb, "block_size_mb")
            self.max_padding_size_mb = check.opt_int_param(
                max_padding_size_mb, "max_padding_size_mb"
            )
            self.page_size_kb = check.opt_int_param(page_size_kb, "page_size_kb")
            self.dictionary_page_size_kb = check.opt_int_param(
                dictionary_page_size_kb, "dictionary_page_size_kb"
            )
            self.dictionary_encoding = check.opt_bool_param(
                dictionary_encoding, "dictionary_encoding"
            )

    def __init__(
        self,
        name: str,
        s3_bucket_name: str,
        s3_bucket_path: str,
        s3_bucket_region: str,
        format: Union[
            AvroApacheAvro,
            CSVCommaSeparatedValues,
            JSONLinesNewlineDelimitedJSON,
            ParquetColumnarStorage,
        ],
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        s3_endpoint: Optional[str] = None,
        s3_path_format: Optional[str] = None,
        file_name_pattern: Optional[str] = None,
    ):
        """
        Airbyte Destination for S3

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/s3
        """
        self.access_key_id = check.opt_str_param(access_key_id, "access_key_id")
        self.secret_access_key = check.opt_str_param(secret_access_key, "secret_access_key")
        self.s3_bucket_name = check.str_param(s3_bucket_name, "s3_bucket_name")
        self.s3_bucket_path = check.str_param(s3_bucket_path, "s3_bucket_path")
        self.s3_bucket_region = check.str_param(s3_bucket_region, "s3_bucket_region")
        self.format = check.inst_param(
            format,
            "format",
            (
                S3Destination.AvroApacheAvro,
                S3Destination.CSVCommaSeparatedValues,
                S3Destination.JSONLinesNewlineDelimitedJSON,
                S3Destination.ParquetColumnarStorage,
            ),
        )
        self.s3_endpoint = check.opt_str_param(s3_endpoint, "s3_endpoint")
        self.s3_path_format = check.opt_str_param(s3_path_format, "s3_path_format")
        self.file_name_pattern = check.opt_str_param(file_name_pattern, "file_name_pattern")
        super().__init__("S3", name)


class AwsDatalakeDestination(GeneratedAirbyteDestination):
    class IAMRole:
        def __init__(self, role_arn: str):
            self.credentials_title = "IAM Role"
            self.role_arn = check.str_param(role_arn, "role_arn")

    class IAMUser:
        def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
            self.credentials_title = "IAM User"
            self.aws_access_key_id = check.str_param(aws_access_key_id, "aws_access_key_id")
            self.aws_secret_access_key = check.str_param(
                aws_secret_access_key, "aws_secret_access_key"
            )

    def __init__(
        self,
        name: str,
        region: str,
        credentials: Union[IAMRole, IAMUser],
        bucket_name: str,
        bucket_prefix: str,
        aws_account_id: Optional[str] = None,
        lakeformation_database_name: Optional[str] = None,
    ):
        """
        Airbyte Destination for Aws Datalake

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/aws-datalake
        """
        self.aws_account_id = check.opt_str_param(aws_account_id, "aws_account_id")
        self.region = check.str_param(region, "region")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (AwsDatalakeDestination.IAMRole, AwsDatalakeDestination.IAMUser),
        )
        self.bucket_name = check.str_param(bucket_name, "bucket_name")
        self.bucket_prefix = check.str_param(bucket_prefix, "bucket_prefix")
        self.lakeformation_database_name = check.opt_str_param(
            lakeformation_database_name, "lakeformation_database_name"
        )
        super().__init__("Aws Datalake", name)


class MssqlDestination(GeneratedAirbyteDestination):
    class Unencrypted:
        def __init__(
            self,
        ):
            self.ssl_method = "unencrypted"

    class EncryptedTrustServerCertificate:
        def __init__(
            self,
        ):
            self.ssl_method = "encrypted_trust_server_certificate"

    class EncryptedVerifyCertificate:
        def __init__(self, hostNameInCertificate: Optional[str] = None):
            self.ssl_method = "encrypted_verify_certificate"
            self.hostNameInCertificate = check.opt_str_param(
                hostNameInCertificate, "hostNameInCertificate"
            )

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        schema: str,
        username: str,
        ssl_method: Union[Unencrypted, EncryptedTrustServerCertificate, EncryptedVerifyCertificate],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Mssql

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mssql
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.schema = check.str_param(schema, "schema")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.ssl_method = check.inst_param(
            ssl_method,
            "ssl_method",
            (
                MssqlDestination.Unencrypted,
                MssqlDestination.EncryptedTrustServerCertificate,
                MssqlDestination.EncryptedVerifyCertificate,
            ),
        )
        super().__init__("Mssql", name)


class PubsubDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, project_id: str, topic_id: str, credentials_json: str):
        """
        Airbyte Destination for Pubsub

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/pubsub
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.topic_id = check.str_param(topic_id, "topic_id")
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        super().__init__("Pubsub", name)


class R2Destination(GeneratedAirbyteDestination):
    class NoCompression:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Bzip2:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Zstandard:
        def __init__(
            self, codec: str, compression_level: int, include_checksum: Optional[bool] = None
        ):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")
            self.include_checksum = check.opt_bool_param(include_checksum, "include_checksum")

    class Snappy:
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        def __init__(
            self,
            format_type: str,
            compression_codec: Union[
                "R2Destination.NoCompression",
                "R2Destination.Deflate",
                "R2Destination.Bzip2",
                "R2Destination.Xz",
                "R2Destination.Zstandard",
                "R2Destination.Snappy",
            ],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression_codec = check.inst_param(
                compression_codec,
                "compression_codec",
                (
                    R2Destination.NoCompression,
                    R2Destination.Deflate,
                    R2Destination.Bzip2,
                    R2Destination.Xz,
                    R2Destination.Zstandard,
                    R2Destination.Snappy,
                ),
            )

    class GZIP:
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        def __init__(
            self,
            format_type: str,
            flattening: str,
            compression: Union["R2Destination.NoCompression", "R2Destination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.flattening = check.str_param(flattening, "flattening")
            self.compression = check.inst_param(
                compression, "compression", (R2Destination.NoCompression, R2Destination.GZIP)
            )

    class JSONLinesNewlineDelimitedJSON:
        def __init__(
            self,
            format_type: str,
            compression: Union["R2Destination.NoCompression", "R2Destination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression = check.inst_param(
                compression, "compression", (R2Destination.NoCompression, R2Destination.GZIP)
            )

    def __init__(
        self,
        name: str,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        s3_bucket_name: str,
        s3_bucket_path: str,
        format: Union[AvroApacheAvro, CSVCommaSeparatedValues, JSONLinesNewlineDelimitedJSON],
        s3_path_format: Optional[str] = None,
        file_name_pattern: Optional[str] = None,
    ):
        """
        Airbyte Destination for R2

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/r2
        """
        self.account_id = check.str_param(account_id, "account_id")
        self.access_key_id = check.str_param(access_key_id, "access_key_id")
        self.secret_access_key = check.str_param(secret_access_key, "secret_access_key")
        self.s3_bucket_name = check.str_param(s3_bucket_name, "s3_bucket_name")
        self.s3_bucket_path = check.str_param(s3_bucket_path, "s3_bucket_path")
        self.format = check.inst_param(
            format,
            "format",
            (
                R2Destination.AvroApacheAvro,
                R2Destination.CSVCommaSeparatedValues,
                R2Destination.JSONLinesNewlineDelimitedJSON,
            ),
        )
        self.s3_path_format = check.opt_str_param(s3_path_format, "s3_path_format")
        self.file_name_pattern = check.opt_str_param(file_name_pattern, "file_name_pattern")
        super().__init__("R2", name)


class JdbcDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        username: str,
        jdbc_url: str,
        password: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        """
        Airbyte Destination for Jdbc

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/postgres
        """
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url = check.str_param(jdbc_url, "jdbc_url")
        self.schema = check.opt_str_param(schema, "schema")
        super().__init__("Jdbc", name)


class KeenDestination(GeneratedAirbyteDestination):
    def __init__(
        self, name: str, project_id: str, api_key: str, infer_timestamp: Optional[bool] = None
    ):
        """
        Airbyte Destination for Keen

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/keen
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.api_key = check.str_param(api_key, "api_key")
        self.infer_timestamp = check.opt_bool_param(infer_timestamp, "infer_timestamp")
        super().__init__("Keen", name)


class TidbDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: Optional[str] = None,
        ssl: Optional[bool] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Tidb

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/tidb
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Tidb", name)


class FirestoreDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, project_id: str, credentials_json: Optional[str] = None):
        """
        Airbyte Destination for Firestore

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/firestore
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.credentials_json = check.opt_str_param(credentials_json, "credentials_json")
        super().__init__("Firestore", name)


class ScyllaDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        keyspace: str,
        username: str,
        password: str,
        address: str,
        port: int,
        replication: Optional[int] = None,
    ):
        """
        Airbyte Destination for Scylla

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/scylla
        """
        self.keyspace = check.str_param(keyspace, "keyspace")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.address = check.str_param(address, "address")
        self.port = check.int_param(port, "port")
        self.replication = check.opt_int_param(replication, "replication")
        super().__init__("Scylla", name)


class RedisDestination(GeneratedAirbyteDestination):
    def __init__(
        self, name: str, host: str, port: int, username: str, password: str, cache_type: str
    ):
        """
        Airbyte Destination for Redis

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redis
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.cache_type = check.str_param(cache_type, "cache_type")
        super().__init__("Redis", name)


class MqttDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        broker_host: str,
        broker_port: int,
        use_tls: bool,
        topic_pattern: str,
        publisher_sync: bool,
        connect_timeout: int,
        automatic_reconnect: bool,
        clean_session: bool,
        message_retained: bool,
        message_qos: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        topic_test: Optional[str] = None,
        client: Optional[str] = None,
    ):
        """
        Airbyte Destination for Mqtt

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mqtt
        """
        self.broker_host = check.str_param(broker_host, "broker_host")
        self.broker_port = check.int_param(broker_port, "broker_port")
        self.use_tls = check.bool_param(use_tls, "use_tls")
        self.username = check.opt_str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.topic_pattern = check.str_param(topic_pattern, "topic_pattern")
        self.topic_test = check.opt_str_param(topic_test, "topic_test")
        self.client = check.opt_str_param(client, "client")
        self.publisher_sync = check.bool_param(publisher_sync, "publisher_sync")
        self.connect_timeout = check.int_param(connect_timeout, "connect_timeout")
        self.automatic_reconnect = check.bool_param(automatic_reconnect, "automatic_reconnect")
        self.clean_session = check.bool_param(clean_session, "clean_session")
        self.message_retained = check.bool_param(message_retained, "message_retained")
        self.message_qos = check.str_param(message_qos, "message_qos")
        super().__init__("Mqtt", name)


class RedshiftDestination(GeneratedAirbyteDestination):
    class Standard:
        def __init__(
            self,
        ):
            self.method = "Standard"

    class NoEncryption:
        def __init__(
            self,
        ):
            self.encryption_type = "none"

    class AESCBCEnvelopeEncryption:
        def __init__(self, key_encrypting_key: Optional[str] = None):
            self.encryption_type = "aes_cbc_envelope"
            self.key_encrypting_key = check.opt_str_param(key_encrypting_key, "key_encrypting_key")

    class S3Staging:
        def __init__(
            self,
            s3_bucket_name: str,
            s3_bucket_region: str,
            access_key_id: str,
            secret_access_key: str,
            encryption: Union[
                "RedshiftDestination.NoEncryption", "RedshiftDestination.AESCBCEnvelopeEncryption"
            ],
            s3_bucket_path: Optional[str] = None,
            file_name_pattern: Optional[str] = None,
            purge_staging_data: Optional[bool] = None,
        ):
            self.method = "S3 Staging"
            self.s3_bucket_name = check.str_param(s3_bucket_name, "s3_bucket_name")
            self.s3_bucket_path = check.opt_str_param(s3_bucket_path, "s3_bucket_path")
            self.s3_bucket_region = check.str_param(s3_bucket_region, "s3_bucket_region")
            self.file_name_pattern = check.opt_str_param(file_name_pattern, "file_name_pattern")
            self.access_key_id = check.str_param(access_key_id, "access_key_id")
            self.secret_access_key = check.str_param(secret_access_key, "secret_access_key")
            self.purge_staging_data = check.opt_bool_param(purge_staging_data, "purge_staging_data")
            self.encryption = check.inst_param(
                encryption,
                "encryption",
                (RedshiftDestination.NoEncryption, RedshiftDestination.AESCBCEnvelopeEncryption),
            )

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        schema: str,
        uploading_method: Union[Standard, S3Staging],
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Redshift

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redshift
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.database = check.str_param(database, "database")
        self.schema = check.str_param(schema, "schema")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.uploading_method = check.inst_param(
            uploading_method,
            "uploading_method",
            (RedshiftDestination.Standard, RedshiftDestination.S3Staging),
        )
        super().__init__("Redshift", name)


class PulsarDestination(GeneratedAirbyteDestination):
    def __init__(
        self,
        name: str,
        brokers: str,
        use_tls: bool,
        topic_type: str,
        topic_tenant: str,
        topic_namespace: str,
        topic_pattern: str,
        compression_type: str,
        send_timeout_ms: int,
        max_pending_messages: int,
        max_pending_messages_across_partitions: int,
        batching_enabled: bool,
        batching_max_messages: int,
        batching_max_publish_delay: int,
        block_if_queue_full: bool,
        topic_test: Optional[str] = None,
        producer_name: Optional[str] = None,
        producer_sync: Optional[bool] = None,
    ):
        """
        Airbyte Destination for Pulsar

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/pulsar
        """
        self.brokers = check.str_param(brokers, "brokers")
        self.use_tls = check.bool_param(use_tls, "use_tls")
        self.topic_type = check.str_param(topic_type, "topic_type")
        self.topic_tenant = check.str_param(topic_tenant, "topic_tenant")
        self.topic_namespace = check.str_param(topic_namespace, "topic_namespace")
        self.topic_pattern = check.str_param(topic_pattern, "topic_pattern")
        self.topic_test = check.opt_str_param(topic_test, "topic_test")
        self.producer_name = check.opt_str_param(producer_name, "producer_name")
        self.producer_sync = check.opt_bool_param(producer_sync, "producer_sync")
        self.compression_type = check.str_param(compression_type, "compression_type")
        self.send_timeout_ms = check.int_param(send_timeout_ms, "send_timeout_ms")
        self.max_pending_messages = check.int_param(max_pending_messages, "max_pending_messages")
        self.max_pending_messages_across_partitions = check.int_param(
            max_pending_messages_across_partitions, "max_pending_messages_across_partitions"
        )
        self.batching_enabled = check.bool_param(batching_enabled, "batching_enabled")
        self.batching_max_messages = check.int_param(batching_max_messages, "batching_max_messages")
        self.batching_max_publish_delay = check.int_param(
            batching_max_publish_delay, "batching_max_publish_delay"
        )
        self.block_if_queue_full = check.bool_param(block_if_queue_full, "block_if_queue_full")
        super().__init__("Pulsar", name)


class SnowflakeDestination(GeneratedAirbyteDestination):
    class OAuth20:
        def __init__(
            self,
            access_token: str,
            refresh_token: str,
            auth_type: Optional[str] = None,
            client_id: Optional[str] = None,
            client_secret: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.client_id = check.opt_str_param(client_id, "client_id")
            self.client_secret = check.opt_str_param(client_secret, "client_secret")
            self.access_token = check.str_param(access_token, "access_token")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    class KeyPairAuthentication:
        def __init__(
            self,
            private_key: str,
            auth_type: Optional[str] = None,
            private_key_password: Optional[str] = None,
        ):
            self.auth_type = check.opt_str_param(auth_type, "auth_type")
            self.private_key = check.str_param(private_key, "private_key")
            self.private_key_password = check.opt_str_param(
                private_key_password, "private_key_password"
            )

    class UsernameAndPassword:
        def __init__(self, password: str):
            self.password = check.str_param(password, "password")

    class SelectAnotherOption:
        def __init__(self, method: str):
            self.method = check.str_param(method, "method")

    class RecommendedInternalStaging:
        def __init__(self, method: str):
            self.method = check.str_param(method, "method")

    class NoEncryption:
        def __init__(
            self,
        ):
            self.encryption_type = "none"

    class AESCBCEnvelopeEncryption:
        def __init__(self, key_encrypting_key: Optional[str] = None):
            self.encryption_type = "aes_cbc_envelope"
            self.key_encrypting_key = check.opt_str_param(key_encrypting_key, "key_encrypting_key")

    class AWSS3Staging:
        def __init__(
            self,
            method: str,
            s3_bucket_name: str,
            access_key_id: str,
            secret_access_key: str,
            encryption: Union[
                "SnowflakeDestination.NoEncryption", "SnowflakeDestination.AESCBCEnvelopeEncryption"
            ],
            s3_bucket_region: Optional[str] = None,
            purge_staging_data: Optional[bool] = None,
            file_name_pattern: Optional[str] = None,
        ):
            self.method = check.str_param(method, "method")
            self.s3_bucket_name = check.str_param(s3_bucket_name, "s3_bucket_name")
            self.s3_bucket_region = check.opt_str_param(s3_bucket_region, "s3_bucket_region")
            self.access_key_id = check.str_param(access_key_id, "access_key_id")
            self.secret_access_key = check.str_param(secret_access_key, "secret_access_key")
            self.purge_staging_data = check.opt_bool_param(purge_staging_data, "purge_staging_data")
            self.encryption = check.inst_param(
                encryption,
                "encryption",
                (SnowflakeDestination.NoEncryption, SnowflakeDestination.AESCBCEnvelopeEncryption),
            )
            self.file_name_pattern = check.opt_str_param(file_name_pattern, "file_name_pattern")

    class GoogleCloudStorageStaging:
        def __init__(self, method: str, project_id: str, bucket_name: str, credentials_json: str):
            self.method = check.str_param(method, "method")
            self.project_id = check.str_param(project_id, "project_id")
            self.bucket_name = check.str_param(bucket_name, "bucket_name")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    class AzureBlobStorageStaging:
        def __init__(
            self,
            method: str,
            azure_blob_storage_account_name: str,
            azure_blob_storage_container_name: str,
            azure_blob_storage_sas_token: str,
            azure_blob_storage_endpoint_domain_name: Optional[str] = None,
        ):
            self.method = check.str_param(method, "method")
            self.azure_blob_storage_endpoint_domain_name = check.opt_str_param(
                azure_blob_storage_endpoint_domain_name, "azure_blob_storage_endpoint_domain_name"
            )
            self.azure_blob_storage_account_name = check.str_param(
                azure_blob_storage_account_name, "azure_blob_storage_account_name"
            )
            self.azure_blob_storage_container_name = check.str_param(
                azure_blob_storage_container_name, "azure_blob_storage_container_name"
            )
            self.azure_blob_storage_sas_token = check.str_param(
                azure_blob_storage_sas_token, "azure_blob_storage_sas_token"
            )

    def __init__(
        self,
        name: str,
        host: str,
        role: str,
        warehouse: str,
        database: str,
        schema: str,
        username: str,
        credentials: Union[OAuth20, KeyPairAuthentication, UsernameAndPassword],
        loading_method: Union[
            SelectAnotherOption,
            RecommendedInternalStaging,
            AWSS3Staging,
            GoogleCloudStorageStaging,
            AzureBlobStorageStaging,
        ],
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Snowflake

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/snowflake
        """
        self.host = check.str_param(host, "host")
        self.role = check.str_param(role, "role")
        self.warehouse = check.str_param(warehouse, "warehouse")
        self.database = check.str_param(database, "database")
        self.schema = check.str_param(schema, "schema")
        self.username = check.str_param(username, "username")
        self.credentials = check.inst_param(
            credentials,
            "credentials",
            (
                SnowflakeDestination.OAuth20,
                SnowflakeDestination.KeyPairAuthentication,
                SnowflakeDestination.UsernameAndPassword,
            ),
        )
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        self.loading_method = check.inst_param(
            loading_method,
            "loading_method",
            (
                SnowflakeDestination.SelectAnotherOption,
                SnowflakeDestination.RecommendedInternalStaging,
                SnowflakeDestination.AWSS3Staging,
                SnowflakeDestination.GoogleCloudStorageStaging,
                SnowflakeDestination.AzureBlobStorageStaging,
            ),
        )
        super().__init__("Snowflake", name)


class PostgresDestination(GeneratedAirbyteDestination):
    class Disable:
        def __init__(
            self,
        ):
            self.mode = "disable"

    class Allow:
        def __init__(
            self,
        ):
            self.mode = "allow"

    class Prefer:
        def __init__(
            self,
        ):
            self.mode = "prefer"

    class Require:
        def __init__(
            self,
        ):
            self.mode = "require"

    class VerifyCa:
        def __init__(self, ca_certificate: str, client_key_password: Optional[str] = None):
            self.mode = "verify-ca"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class VerifyFull:
        def __init__(
            self,
            ca_certificate: str,
            client_certificate: str,
            client_key: str,
            client_key_password: Optional[str] = None,
        ):
            self.mode = "verify-full"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_certificate = check.str_param(client_certificate, "client_certificate")
            self.client_key = check.str_param(client_key, "client_key")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        schema: str,
        username: str,
        ssl_mode: Union[Disable, Allow, Prefer, Require, VerifyCa, VerifyFull],
        password: Optional[str] = None,
        ssl: Optional[bool] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """
        Airbyte Destination for Postgres

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/postgres
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.schema = check.str_param(schema, "schema")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.ssl = check.opt_bool_param(ssl, "ssl")
        self.ssl_mode = check.inst_param(
            ssl_mode,
            "ssl_mode",
            (
                PostgresDestination.Disable,
                PostgresDestination.Allow,
                PostgresDestination.Prefer,
                PostgresDestination.Require,
                PostgresDestination.VerifyCa,
                PostgresDestination.VerifyFull,
            ),
        )
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Postgres", name)


class ScaffoldDestinationPythonDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, TODO: Optional[str] = None):
        """
        Airbyte Destination for Scaffold Destination Python

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/scaffold-destination-python
        """
        self.TODO = check.opt_str_param(TODO, "TODO")
        super().__init__("Scaffold Destination Python", name)


class LocalJsonDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, destination_path: str):
        """
        Airbyte Destination for Local Json

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/local-json
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Local Json", name)


class MeilisearchDestination(GeneratedAirbyteDestination):
    def __init__(self, name: str, host: str, api_key: Optional[str] = None):
        """
        Airbyte Destination for Meilisearch

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/meilisearch
        """
        self.host = check.str_param(host, "host")
        self.api_key = check.opt_str_param(api_key, "api_key")
        super().__init__("Meilisearch", name)
