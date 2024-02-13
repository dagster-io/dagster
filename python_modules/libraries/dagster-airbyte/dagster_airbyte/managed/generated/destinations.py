# ruff: noqa: A001, A002
from typing import Optional, Union

import dagster._check as check
from dagster._annotations import public

from dagster_airbyte.managed.types import GeneratedAirbyteDestination


class DynamodbDestination(GeneratedAirbyteDestination):
    @public
    def __init__(
        self,
        name: str,
        dynamodb_table_name_prefix: str,
        dynamodb_region: str,
        access_key_id: str,
        secret_access_key: str,
        dynamodb_endpoint: Optional[str] = None,
    ):
        """Airbyte Destination for Dynamodb.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/dynamodb

        Args:
            name (str): The name of the destination.
            dynamodb_endpoint (Optional[str]): This is your DynamoDB endpoint url.(if you are working with AWS DynamoDB, just leave empty).
            dynamodb_table_name_prefix (str): The prefix to use when naming DynamoDB tables.
            dynamodb_region (str): The region of the DynamoDB.
            access_key_id (str): The access key id to access the DynamoDB. Airbyte requires Read and Write permissions to the DynamoDB.
            secret_access_key (str): The corresponding secret to the access key id.
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
        @public
        def __init__(
            self,
        ):
            self.method = "Standard"

    class HMACKey:
        @public
        def __init__(self, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = "HMAC_KEY"
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class GCSStaging:
        @public
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

    @public
    def __init__(
        self,
        name: str,
        project_id: str,
        dataset_location: str,
        dataset_id: str,
        loading_method: Union[
            "BigqueryDestination.StandardInserts", "BigqueryDestination.GCSStaging"
        ],
        credentials_json: Optional[str] = None,
        transformation_priority: Optional[str] = None,
        big_query_client_buffer_size_mb: Optional[int] = None,
    ):
        """Airbyte Destination for Bigquery.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/bigquery

        Args:
            name (str): The name of the destination.
            project_id (str): The GCP project ID for the project containing the target BigQuery dataset. Read more here.
            dataset_location (str): The location of the dataset. Warning: Changes made after creation will not be applied. Read more here.
            dataset_id (str): The default BigQuery Dataset ID that tables are replicated to if the source does not specify a namespace. Read more here.
            loading_method (Union[BigqueryDestination.StandardInserts, BigqueryDestination.GCSStaging]): Loading method used to send select the way data will be uploaded to BigQuery. Standard Inserts - Direct uploading using SQL INSERT statements. This method is extremely inefficient and provided only for quick testing. In almost all cases, you should use staging. GCS Staging - Writes large batches of records to a file, uploads the file to GCS, then uses COPY INTO table to upload the file. Recommended for most workloads for better speed and scalability. Read more about GCS Staging here.
            credentials_json (Optional[str]): The contents of the JSON service account key. Check out the docs if you need help generating this key. Default credentials will be used if this field is left empty.
            transformation_priority (Optional[str]): Interactive run type means that the query is executed as soon as possible, and these queries count towards concurrent rate limit and daily limit. Read more about interactive run type here. Batch queries are queued and started as soon as idle resources are available in the BigQuery shared resource pool, which usually occurs within a few minutes. Batch queries don`t count towards your concurrent rate limit. Read more about batch queries here. The default "interactive" value is used if not set explicitly.
            big_query_client_buffer_size_mb (Optional[int]): Google BigQuery client's chunk (buffer) size (MIN=1, MAX = 15) for each table. The size that will be written by a single RPC. Written data will be buffered and only flushed upon reaching this size or closing the channel. The default 15MB value is used if not set explicitly. Read more here.
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
    @public
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
        """Airbyte Destination for Rabbitmq.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/rabbitmq

        Args:
            name (str): The name of the destination.
            ssl (Optional[bool]): SSL enabled.
            host (str): The RabbitMQ host name.
            port (Optional[int]): The RabbitMQ port.
            virtual_host (Optional[str]): The RabbitMQ virtual host name.
            username (Optional[str]): The username to connect.
            password (Optional[str]): The password to connect.
            exchange (Optional[str]): The exchange name.
            routing_key (str): The routing key.
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
    @public
    def __init__(self, name: str, bucket_id: str, secret_key: str):
        """Airbyte Destination for Kvdb.

        Documentation can be found at https://kvdb.io/docs/api/

        Args:
            name (str): The name of the destination.
            bucket_id (str): The ID of your KVdb bucket.
            secret_key (str): Your bucket Secret Key.
        """
        self.bucket_id = check.str_param(bucket_id, "bucket_id")
        self.secret_key = check.str_param(secret_key, "secret_key")
        super().__init__("Kvdb", name)


class ClickhouseDestination(GeneratedAirbyteDestination):
    @public
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
        """Airbyte Destination for Clickhouse.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/clickhouse

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): HTTP port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            ssl (Optional[bool]): Encrypt data using SSL.
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
    @public
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
        """Airbyte Destination for Amazon Sqs.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/amazon-sqs

        Args:
            name (str): The name of the destination.
            queue_url (str): URL of the SQS Queue
            region (str): AWS Region of the SQS Queue
            message_delay (Optional[int]): Modify the Message Delay of the individual message from the Queue's default (seconds).
            access_key (Optional[str]): The Access Key ID of the AWS IAM Role to use for sending  messages
            secret_key (Optional[str]): The Secret Key of the AWS IAM Role to use for sending messages
            message_body_key (Optional[str]): Use this property to extract the contents of the named key in the input record to use as the SQS message body. If not set, the entire content of the input record data is used as the message body.
            message_group_id (Optional[str]): The tag that specifies that a message belongs to a specific message group. This parameter applies only to, and is REQUIRED by, FIFO queues.
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
    @public
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
        """Airbyte Destination for Mariadb Columnstore.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mariadb-columnstore

        Args:
            name (str): The name of the destination.
            host (str): The Hostname of the database.
            port (int): The Port of the database.
            database (str): Name of the database.
            username (str): The Username which is used to access the database.
            password (Optional[str]): The Password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.database = check.str_param(database, "database")
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url_params = check.opt_str_param(jdbc_url_params, "jdbc_url_params")
        super().__init__("Mariadb Columnstore", name)


class KinesisDestination(GeneratedAirbyteDestination):
    @public
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
        """Airbyte Destination for Kinesis.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/kinesis

        Args:
            name (str): The name of the destination.
            endpoint (str): AWS Kinesis endpoint.
            region (str): AWS region. Your account determines the Regions that are available to you.
            shardCount (int): Number of shards to which the data should be streamed.
            accessKey (str): Generate the AWS Access Key for current user.
            privateKey (str): The AWS Private Key - a string of numbers and letters that are unique for each account, also known as a "recovery phrase".
            bufferSize (int): Buffer size for storing kinesis records before being batch streamed.
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
        @public
        def __init__(self, flattening: str):
            self.format_type = "CSV"
            self.flattening = check.str_param(flattening, "flattening")

    class JSONLinesNewlineDelimitedJSON:
        @public
        def __init__(
            self,
        ):
            self.format_type = "JSONL"

    @public
    def __init__(
        self,
        name: str,
        azure_blob_storage_account_name: str,
        azure_blob_storage_account_key: str,
        format: Union[
            "AzureBlobStorageDestination.CSVCommaSeparatedValues",
            "AzureBlobStorageDestination.JSONLinesNewlineDelimitedJSON",
        ],
        azure_blob_storage_endpoint_domain_name: Optional[str] = None,
        azure_blob_storage_container_name: Optional[str] = None,
        azure_blob_storage_output_buffer_size: Optional[int] = None,
    ):
        """Airbyte Destination for Azure Blob Storage.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/azureblobstorage

        Args:
            name (str): The name of the destination.
            azure_blob_storage_endpoint_domain_name (Optional[str]): This is Azure Blob Storage endpoint domain name. Leave default value (or leave it empty if run container from command line) to use Microsoft native from example.
            azure_blob_storage_container_name (Optional[str]): The name of the Azure blob storage container. If not exists - will be created automatically. May be empty, then will be created automatically airbytecontainer+timestamp
            azure_blob_storage_account_name (str): The account's name of the Azure Blob Storage.
            azure_blob_storage_account_key (str): The Azure blob storage account key.
            azure_blob_storage_output_buffer_size (Optional[int]): The amount of megabytes to buffer for the output stream to Azure. This will impact memory footprint on workers, but may need adjustment for performance and appropriate block size in Azure.
            format (Union[AzureBlobStorageDestination.CSVCommaSeparatedValues, AzureBlobStorageDestination.JSONLinesNewlineDelimitedJSON]): Output data format
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
        @public
        def __init__(self, security_protocol: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")

    class SASLPLAINTEXT:
        @public
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    class SASLSSL:
        @public
        def __init__(self, security_protocol: str, sasl_mechanism: str, sasl_jaas_config: str):
            self.security_protocol = check.str_param(security_protocol, "security_protocol")
            self.sasl_mechanism = check.str_param(sasl_mechanism, "sasl_mechanism")
            self.sasl_jaas_config = check.str_param(sasl_jaas_config, "sasl_jaas_config")

    @public
    def __init__(
        self,
        name: str,
        bootstrap_servers: str,
        topic_pattern: str,
        protocol: Union[
            "KafkaDestination.PLAINTEXT",
            "KafkaDestination.SASLPLAINTEXT",
            "KafkaDestination.SASLSSL",
        ],
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
        """Airbyte Destination for Kafka.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/kafka

        Args:
            name (str): The name of the destination.
            bootstrap_servers (str): A list of host/port pairs to use for establishing the initial connection to the Kafka cluster. The client will make use of all servers irrespective of which servers are specified here for bootstrapping&mdash;this list only impacts the initial hosts used to discover the full set of servers. This list should be in the form host1:port1,host2:port2,.... Since these servers are just used for the initial connection to discover the full cluster membership (which may change dynamically), this list need not contain the full set of servers (you may want more than one, though, in case a server is down).
            topic_pattern (str): Topic pattern in which the records will be sent. You can use patterns like '{namespace}' and/or '{stream}' to send the message to a specific topic based on these values. Notice that the topic name will be transformed to a standard naming convention.
            test_topic (Optional[str]): Topic to test if Airbyte can produce messages.
            sync_producer (Optional[bool]): Wait synchronously until the record has been sent to Kafka.
            protocol (Union[KafkaDestination.PLAINTEXT, KafkaDestination.SASLPLAINTEXT, KafkaDestination.SASLSSL]): Protocol used to communicate with brokers.
            client_id (Optional[str]): An ID string to pass to the server when making requests. The purpose of this is to be able to track the source of requests beyond just ip/port by allowing a logical application name to be included in server-side request logging.
            acks (str): The number of acknowledgments the producer requires the leader to have received before considering a request complete. This controls the  durability of records that are sent.
            enable_idempotence (bool): When set to 'true', the producer will ensure that exactly one copy of each message is written in the stream. If 'false', producer retries due to broker failures, etc., may write duplicates of the retried message in the stream.
            compression_type (str): The compression type for all data generated by the producer.
            batch_size (int): The producer will attempt to batch records together into fewer requests whenever multiple records are being sent to the same partition.
            linger_ms (str): The producer groups together any records that arrive in between request transmissions into a single batched request.
            max_in_flight_requests_per_connection (int): The maximum number of unacknowledged requests the client will send on a single connection before blocking. Can be greater than 1, and the maximum value supported with idempotency is 5.
            client_dns_lookup (str): Controls how the client uses DNS lookups. If set to use_all_dns_ips, connect to each returned IP address in sequence until a successful connection is established. After a disconnection, the next IP is used. Once all IPs have been used once, the client resolves the IP(s) from the hostname again. If set to resolve_canonical_bootstrap_servers_only, resolve each bootstrap address into a list of canonical names. After the bootstrap phase, this behaves the same as use_all_dns_ips. If set to default (deprecated), attempt to connect to the first IP address returned by the lookup, even if the lookup returns multiple IP addresses.
            buffer_memory (str): The total bytes of memory the producer can use to buffer records waiting to be sent to the server.
            max_request_size (int): The maximum size of a request in bytes.
            retries (int): Setting a value greater than zero will cause the client to resend any record whose send fails with a potentially transient error.
            socket_connection_setup_timeout_ms (str): The amount of time the client will wait for the socket connection to be established.
            socket_connection_setup_timeout_max_ms (str): The maximum amount of time the client will wait for the socket connection to be established. The connection setup timeout will increase exponentially for each consecutive connection failure up to this maximum.
            max_block_ms (str): The configuration controls how long the KafkaProducer's send(), partitionsFor(), initTransactions(), sendOffsetsToTransaction(), commitTransaction() and abortTransaction() methods will block.
            request_timeout_ms (int): The configuration controls the maximum amount of time the client will wait for the response of a request. If the response is not received before the timeout elapses the client will resend the request if necessary or fail the request if retries are exhausted.
            delivery_timeout_ms (int): An upper bound on the time to report success or failure after a call to 'send()' returns.
            send_buffer_bytes (int): The size of the TCP send buffer (SO_SNDBUF) to use when sending data. If the value is -1, the OS default will be used.
            receive_buffer_bytes (int): The size of the TCP receive buffer (SO_RCVBUF) to use when reading data. If the value is -1, the OS default will be used.
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
        @public
        def __init__(
            self,
        ):
            self.method = "none"

    class ApiKeySecret:
        @public
        def __init__(self, apiKeyId: str, apiKeySecret: str):
            self.method = "secret"
            self.apiKeyId = check.str_param(apiKeyId, "apiKeyId")
            self.apiKeySecret = check.str_param(apiKeySecret, "apiKeySecret")

    class UsernamePassword:
        @public
        def __init__(self, username: str, password: str):
            self.method = "basic"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    @public
    def __init__(
        self,
        name: str,
        endpoint: str,
        authenticationMethod: Union[
            "ElasticsearchDestination.None_",
            "ElasticsearchDestination.ApiKeySecret",
            "ElasticsearchDestination.UsernamePassword",
        ],
        upsert: Optional[bool] = None,
    ):
        r"""Airbyte Destination for Elasticsearch.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/elasticsearch

        Args:
            name (str): The name of the destination.
            endpoint (str): The full url of the Elasticsearch server
            upsert (Optional[bool]): If a primary key identifier is defined in the source, an upsert will be performed using the primary key value as the elasticsearch doc id. Does not support composite primary keys.
            authenticationMethod (Union[ElasticsearchDestination.None\\_, ElasticsearchDestination.ApiKeySecret, ElasticsearchDestination.UsernamePassword]): The type of authentication to be used
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
    @public
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
        """Airbyte Destination for Mysql.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mysql

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            ssl (Optional[bool]): Encrypt data using SSL.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
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
    @public
    def __init__(
        self,
        name: str,
        host: str,
        username: str,
        password: str,
        destination_path: str,
        port: Optional[int] = None,
    ):
        """Airbyte Destination for Sftp Json.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/sftp-json

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the SFTP server.
            port (Optional[int]): Port of the SFTP server.
            username (str): Username to use to access the SFTP server.
            password (str): Password associated with the username.
            destination_path (str): Path to the directory where json files will be written.
        """
        self.host = check.str_param(host, "host")
        self.port = check.opt_int_param(port, "port")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Sftp Json", name)


class GcsDestination(GeneratedAirbyteDestination):
    class HMACKey:
        @public
        def __init__(self, credential_type: str, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = check.str_param(credential_type, "credential_type")
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class NoCompression:
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        @public
        def __init__(self, codec: str, compression_level: Optional[int] = None):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.opt_int_param(compression_level, "compression_level")

    class Bzip2:
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        @public
        def __init__(self, codec: str, compression_level: Optional[int] = None):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.opt_int_param(compression_level, "compression_level")

    class Zstandard:
        @public
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
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        @public
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
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        @public
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
        @public
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
        @public
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

    @public
    def __init__(
        self,
        name: str,
        gcs_bucket_name: str,
        gcs_bucket_path: str,
        credential: "GcsDestination.HMACKey",
        format: Union[
            "GcsDestination.AvroApacheAvro",
            "GcsDestination.CSVCommaSeparatedValues",
            "GcsDestination.JSONLinesNewlineDelimitedJSON",
            "GcsDestination.ParquetColumnarStorage",
        ],
        gcs_bucket_region: Optional[str] = None,
    ):
        """Airbyte Destination for Gcs.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/gcs

        Args:
            name (str): The name of the destination.
            gcs_bucket_name (str): You can find the bucket name in the App Engine Admin console Application Settings page, under the label Google Cloud Storage Bucket. Read more here.
            gcs_bucket_path (str): GCS Bucket Path string Subdirectory under the above bucket to sync the data into.
            gcs_bucket_region (Optional[str]): Select a Region of the GCS Bucket. Read more here.
            credential (GcsDestination.HMACKey): An HMAC key is a type of credential and can be associated with a service account or a user account in Cloud Storage. Read more here.
            format (Union[GcsDestination.AvroApacheAvro, GcsDestination.CSVCommaSeparatedValues, GcsDestination.JSONLinesNewlineDelimitedJSON, GcsDestination.ParquetColumnarStorage]): Output data format. One of the following formats must be selected - AVRO format, PARQUET format, CSV format, or JSONL format.
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
    @public
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
        """Airbyte Destination for Cassandra.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/cassandra

        Args:
            name (str): The name of the destination.
            keyspace (str): Default Cassandra keyspace to create data in.
            username (str): Username to use to access Cassandra.
            password (str): Password associated with Cassandra.
            address (str): Address to connect to.
            port (int): Port of Cassandra.
            datacenter (Optional[str]): Datacenter of the cassandra cluster.
            replication (Optional[int]): Indicates to how many nodes the data should be replicated to.
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
        @public
        def __init__(
            self,
        ):
            self.method = "SQL"

    class ExternalTableViaS3:
        @public
        def __init__(self, s3_bucket: str, s3_region: str, aws_key_id: str, aws_key_secret: str):
            self.method = "S3"
            self.s3_bucket = check.str_param(s3_bucket, "s3_bucket")
            self.s3_region = check.str_param(s3_region, "s3_region")
            self.aws_key_id = check.str_param(aws_key_id, "aws_key_id")
            self.aws_key_secret = check.str_param(aws_key_secret, "aws_key_secret")

    @public
    def __init__(
        self,
        name: str,
        username: str,
        password: str,
        database: str,
        loading_method: Union[
            "FireboltDestination.SQLInserts", "FireboltDestination.ExternalTableViaS3"
        ],
        account: Optional[str] = None,
        host: Optional[str] = None,
        engine: Optional[str] = None,
    ):
        """Airbyte Destination for Firebolt.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/firebolt

        Args:
            name (str): The name of the destination.
            username (str): Firebolt email address you use to login.
            password (str): Firebolt password.
            account (Optional[str]): Firebolt account to login.
            host (Optional[str]): The host name of your Firebolt database.
            database (str): The database to connect to.
            engine (Optional[str]): Engine name or url to connect to.
            loading_method (Union[FireboltDestination.SQLInserts, FireboltDestination.ExternalTableViaS3]): Loading method used to select the way data will be uploaded to Firebolt
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
        @public
        def __init__(self, client_id: str, client_secret: str, refresh_token: str):
            self.client_id = check.str_param(client_id, "client_id")
            self.client_secret = check.str_param(client_secret, "client_secret")
            self.refresh_token = check.str_param(refresh_token, "refresh_token")

    @public
    def __init__(
        self,
        name: str,
        spreadsheet_id: str,
        credentials: "GoogleSheetsDestination.AuthenticationViaGoogleOAuth",
    ):
        """Airbyte Destination for Google Sheets.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/google-sheets

        Args:
            name (str): The name of the destination.
            spreadsheet_id (str): The link to your spreadsheet. See this guide for more details.
            credentials (GoogleSheetsDestination.AuthenticationViaGoogleOAuth): Google API Credentials for connecting to Google Sheets and Google Drive APIs
        """
        self.spreadsheet_id = check.str_param(spreadsheet_id, "spreadsheet_id")
        self.credentials = check.inst_param(
            credentials, "credentials", GoogleSheetsDestination.AuthenticationViaGoogleOAuth
        )
        super().__init__("Google Sheets", name)


class DatabricksDestination(GeneratedAirbyteDestination):
    class AmazonS3:
        @public
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
        @public
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

    @public
    def __init__(
        self,
        name: str,
        accept_terms: bool,
        databricks_server_hostname: str,
        databricks_http_path: str,
        databricks_personal_access_token: str,
        data_source: Union[
            "DatabricksDestination.AmazonS3", "DatabricksDestination.AzureBlobStorage"
        ],
        databricks_port: Optional[str] = None,
        database_schema: Optional[str] = None,
        purge_staging_data: Optional[bool] = None,
    ):
        """Airbyte Destination for Databricks.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/databricks

        Args:
            name (str): The name of the destination.
            accept_terms (bool): You must agree to the Databricks JDBC Driver Terms & Conditions to use this connector.
            databricks_server_hostname (str): Databricks Cluster Server Hostname.
            databricks_http_path (str): Databricks Cluster HTTP Path.
            databricks_port (Optional[str]): Databricks Cluster Port.
            databricks_personal_access_token (str): Databricks Personal Access Token for making authenticated requests.
            database_schema (Optional[str]): The default schema tables are written to if the source does not specify a namespace. Unless specifically configured, the usual value for this field is "public".
            data_source (Union[DatabricksDestination.AmazonS3, DatabricksDestination.AzureBlobStorage]): Storage on which the delta lake is built.
            purge_staging_data (Optional[bool]): Default to 'true'. Switch it to 'false' for debugging purpose.
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
        @public
        def __init__(
            self,
        ):
            self.method = "Standard"

    class HMACKey:
        @public
        def __init__(self, hmac_key_access_id: str, hmac_key_secret: str):
            self.credential_type = "HMAC_KEY"
            self.hmac_key_access_id = check.str_param(hmac_key_access_id, "hmac_key_access_id")
            self.hmac_key_secret = check.str_param(hmac_key_secret, "hmac_key_secret")

    class GCSStaging:
        @public
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

    @public
    def __init__(
        self,
        name: str,
        project_id: str,
        dataset_id: str,
        loading_method: Union[
            "BigqueryDenormalizedDestination.StandardInserts",
            "BigqueryDenormalizedDestination.GCSStaging",
        ],
        credentials_json: Optional[str] = None,
        dataset_location: Optional[str] = None,
        big_query_client_buffer_size_mb: Optional[int] = None,
    ):
        """Airbyte Destination for Bigquery Denormalized.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/bigquery

        Args:
            name (str): The name of the destination.
            project_id (str): The GCP project ID for the project containing the target BigQuery dataset. Read more here.
            dataset_id (str): The default BigQuery Dataset ID that tables are replicated to if the source does not specify a namespace. Read more here.
            loading_method (Union[BigqueryDenormalizedDestination.StandardInserts, BigqueryDenormalizedDestination.GCSStaging]): Loading method used to send select the way data will be uploaded to BigQuery. Standard Inserts - Direct uploading using SQL INSERT statements. This method is extremely inefficient and provided only for quick testing. In almost all cases, you should use staging. GCS Staging - Writes large batches of records to a file, uploads the file to GCS, then uses COPY INTO table to upload the file. Recommended for most workloads for better speed and scalability. Read more about GCS Staging here.
            credentials_json (Optional[str]): The contents of the JSON service account key. Check out the docs if you need help generating this key. Default credentials will be used if this field is left empty.
            dataset_location (Optional[str]): The location of the dataset. Warning: Changes made after creation will not be applied. The default "US" value is used if not set explicitly. Read more here.
            big_query_client_buffer_size_mb (Optional[int]): Google BigQuery client's chunk (buffer) size (MIN=1, MAX = 15) for each table. The size that will be written by a single RPC. Written data will be buffered and only flushed upon reaching this size or closing the channel. The default 15MB value is used if not set explicitly. Read more here.
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
    @public
    def __init__(self, name: str, destination_path: str):
        """Airbyte Destination for Sqlite.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/sqlite

        Args:
            name (str): The name of the destination.
            destination_path (str): Path to the sqlite.db file. The file will be placed inside that local mount. For more information check out our docs
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Sqlite", name)


class MongodbDestination(GeneratedAirbyteDestination):
    class StandaloneMongoDbInstance:
        @public
        def __init__(self, instance: str, host: str, port: int, tls: Optional[bool] = None):
            self.instance = check.str_param(instance, "instance")
            self.host = check.str_param(host, "host")
            self.port = check.int_param(port, "port")
            self.tls = check.opt_bool_param(tls, "tls")

    class ReplicaSet:
        @public
        def __init__(self, instance: str, server_addresses: str, replica_set: Optional[str] = None):
            self.instance = check.str_param(instance, "instance")
            self.server_addresses = check.str_param(server_addresses, "server_addresses")
            self.replica_set = check.opt_str_param(replica_set, "replica_set")

    class MongoDBAtlas:
        @public
        def __init__(self, instance: str, cluster_url: str):
            self.instance = check.str_param(instance, "instance")
            self.cluster_url = check.str_param(cluster_url, "cluster_url")

    class None_:
        @public
        def __init__(
            self,
        ):
            self.authorization = "none"

    class LoginPassword:
        @public
        def __init__(self, username: str, password: str):
            self.authorization = "login/password"
            self.username = check.str_param(username, "username")
            self.password = check.str_param(password, "password")

    @public
    def __init__(
        self,
        name: str,
        instance_type: Union[
            "MongodbDestination.StandaloneMongoDbInstance",
            "MongodbDestination.ReplicaSet",
            "MongodbDestination.MongoDBAtlas",
        ],
        database: str,
        auth_type: Union["MongodbDestination.None_", "MongodbDestination.LoginPassword"],
    ):
        r"""Airbyte Destination for Mongodb.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mongodb

        Args:
            name (str): The name of the destination.
            instance_type (Union[MongodbDestination.StandaloneMongoDbInstance, MongodbDestination.ReplicaSet, MongodbDestination.MongoDBAtlas]): MongoDb instance to connect to. For MongoDB Atlas and Replica Set TLS connection is used by default.
            database (str): Name of the database.
            auth_type (Union[MongodbDestination.None\\_, MongodbDestination.LoginPassword]): Authorization type.
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
    @public
    def __init__(self, name: str, api_key: str, workspace: str, api_server: Optional[str] = None):
        """Airbyte Destination for Rockset.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/rockset

        Args:
            name (str): The name of the destination.
            api_key (str): Rockset api key
            workspace (str): The Rockset workspace in which collections will be created + written to.
            api_server (Optional[str]): Rockset api URL
        """
        self.api_key = check.str_param(api_key, "api_key")
        self.workspace = check.str_param(workspace, "workspace")
        self.api_server = check.opt_str_param(api_server, "api_server")
        super().__init__("Rockset", name)


class OracleDestination(GeneratedAirbyteDestination):
    class Unencrypted:
        @public
        def __init__(
            self,
        ):
            self.encryption_method = "unencrypted"

    class NativeNetworkEncryptionNNE:
        @public
        def __init__(self, encryption_algorithm: Optional[str] = None):
            self.encryption_method = "client_nne"
            self.encryption_algorithm = check.opt_str_param(
                encryption_algorithm, "encryption_algorithm"
            )

    class TLSEncryptedVerifyCertificate:
        @public
        def __init__(self, ssl_certificate: str):
            self.encryption_method = "encrypted_verify_certificate"
            self.ssl_certificate = check.str_param(ssl_certificate, "ssl_certificate")

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        sid: str,
        username: str,
        encryption: Union[
            "OracleDestination.Unencrypted",
            "OracleDestination.NativeNetworkEncryptionNNE",
            "OracleDestination.TLSEncryptedVerifyCertificate",
        ],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        """Airbyte Destination for Oracle.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/oracle

        Args:
            name (str): The name of the destination.
            host (str): The hostname of the database.
            port (int): The port of the database.
            sid (str): The System Identifier uniquely distinguishes the instance from any other instance on the same computer.
            username (str): The username to access the database. This user must have CREATE USER privileges in the database.
            password (Optional[str]): The password associated with the username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            schema (Optional[str]): The default schema is used as the target schema for all statements issued from the connection that do not explicitly specify a schema name. The usual value for this field is "airbyte".  In Oracle, schemas and users are the same thing, so the "user" parameter is used as the login credentials and this is used for the default Airbyte message schema.
            encryption (Union[OracleDestination.Unencrypted, OracleDestination.NativeNetworkEncryptionNNE, OracleDestination.TLSEncryptedVerifyCertificate]): The encryption method which is used when communicating with the database.
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
    @public
    def __init__(self, name: str, destination_path: str):
        """Airbyte Destination for Csv.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/local-csv

        Args:
            name (str): The name of the destination.
            destination_path (str): Path to the directory where csv files will be written. The destination uses the local mount "/local" and any data files will be placed inside that local mount. For more information check out our docs
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Csv", name)


class S3Destination(GeneratedAirbyteDestination):
    class NoCompression:
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        @public
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Bzip2:
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        @public
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Zstandard:
        @public
        def __init__(
            self, codec: str, compression_level: int, include_checksum: Optional[bool] = None
        ):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")
            self.include_checksum = check.opt_bool_param(include_checksum, "include_checksum")

    class Snappy:
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        @public
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
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        @public
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
        @public
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
        @public
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

    @public
    def __init__(
        self,
        name: str,
        s3_bucket_name: str,
        s3_bucket_path: str,
        s3_bucket_region: str,
        format: Union[
            "S3Destination.AvroApacheAvro",
            "S3Destination.CSVCommaSeparatedValues",
            "S3Destination.JSONLinesNewlineDelimitedJSON",
            "S3Destination.ParquetColumnarStorage",
        ],
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        s3_endpoint: Optional[str] = None,
        s3_path_format: Optional[str] = None,
        file_name_pattern: Optional[str] = None,
    ):
        """Airbyte Destination for S3.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/s3

        Args:
            name (str): The name of the destination.
            access_key_id (Optional[str]): The access key ID to access the S3 bucket. Airbyte requires Read and Write permissions to the given bucket. Read more here.
            secret_access_key (Optional[str]): The corresponding secret to the access key ID. Read more here
            s3_bucket_name (str): The name of the S3 bucket. Read more here.
            s3_bucket_path (str): Directory under the S3 bucket where data will be written. Read more here
            s3_bucket_region (str): The region of the S3 bucket. See here for all region codes.
            format (Union[S3Destination.AvroApacheAvro, S3Destination.CSVCommaSeparatedValues, S3Destination.JSONLinesNewlineDelimitedJSON, S3Destination.ParquetColumnarStorage]): Format of the data output. See here for more details
            s3_endpoint (Optional[str]): Your S3 endpoint url. Read more here
            s3_path_format (Optional[str]): Format string on how data will be organized inside the S3 bucket directory. Read more here
            file_name_pattern (Optional[str]): The pattern allows you to set the file-name format for the S3 staging file(s)
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
        @public
        def __init__(self, role_arn: str):
            self.credentials_title = "IAM Role"
            self.role_arn = check.str_param(role_arn, "role_arn")

    class IAMUser:
        @public
        def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
            self.credentials_title = "IAM User"
            self.aws_access_key_id = check.str_param(aws_access_key_id, "aws_access_key_id")
            self.aws_secret_access_key = check.str_param(
                aws_secret_access_key, "aws_secret_access_key"
            )

    @public
    def __init__(
        self,
        name: str,
        region: str,
        credentials: Union["AwsDatalakeDestination.IAMRole", "AwsDatalakeDestination.IAMUser"],
        bucket_name: str,
        bucket_prefix: str,
        aws_account_id: Optional[str] = None,
        lakeformation_database_name: Optional[str] = None,
    ):
        """Airbyte Destination for Aws Datalake.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/aws-datalake

        Args:
            name (str): The name of the destination.
            aws_account_id (Optional[str]): target aws account id
            region (str): Region name
            credentials (Union[AwsDatalakeDestination.IAMRole, AwsDatalakeDestination.IAMUser]): Choose How to Authenticate to AWS.
            bucket_name (str): Name of the bucket
            bucket_prefix (str): S3 prefix
            lakeformation_database_name (Optional[str]): Which database to use
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
        @public
        def __init__(
            self,
        ):
            self.ssl_method = "unencrypted"

    class EncryptedTrustServerCertificate:
        @public
        def __init__(
            self,
        ):
            self.ssl_method = "encrypted_trust_server_certificate"

    class EncryptedVerifyCertificate:
        @public
        def __init__(self, hostNameInCertificate: Optional[str] = None):
            self.ssl_method = "encrypted_verify_certificate"
            self.hostNameInCertificate = check.opt_str_param(
                hostNameInCertificate, "hostNameInCertificate"
            )

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        schema: str,
        username: str,
        ssl_method: Union[
            "MssqlDestination.Unencrypted",
            "MssqlDestination.EncryptedTrustServerCertificate",
            "MssqlDestination.EncryptedVerifyCertificate",
        ],
        password: Optional[str] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Destination for Mssql.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mssql

        Args:
            name (str): The name of the destination.
            host (str): The host name of the MSSQL database.
            port (int): The port of the MSSQL database.
            database (str): The name of the MSSQL database.
            schema (str): The default schema tables are written to if the source does not specify a namespace. The usual value for this field is "public".
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with this username.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            ssl_method (Union[MssqlDestination.Unencrypted, MssqlDestination.EncryptedTrustServerCertificate, MssqlDestination.EncryptedVerifyCertificate]): The encryption method which is used to communicate with the database.
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
    @public
    def __init__(self, name: str, project_id: str, topic_id: str, credentials_json: str):
        """Airbyte Destination for Pubsub.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/pubsub

        Args:
            name (str): The name of the destination.
            project_id (str): The GCP project ID for the project containing the target PubSub.
            topic_id (str): The PubSub topic ID in the given GCP project ID.
            credentials_json (str): The contents of the JSON service account key. Check out the docs if you need help generating this key.
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.topic_id = check.str_param(topic_id, "topic_id")
        self.credentials_json = check.str_param(credentials_json, "credentials_json")
        super().__init__("Pubsub", name)


class R2Destination(GeneratedAirbyteDestination):
    class NoCompression:
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class Deflate:
        @public
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Bzip2:
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class Xz:
        @public
        def __init__(self, codec: str, compression_level: int):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")

    class Zstandard:
        @public
        def __init__(
            self, codec: str, compression_level: int, include_checksum: Optional[bool] = None
        ):
            self.codec = check.str_param(codec, "codec")
            self.compression_level = check.int_param(compression_level, "compression_level")
            self.include_checksum = check.opt_bool_param(include_checksum, "include_checksum")

    class Snappy:
        @public
        def __init__(self, codec: str):
            self.codec = check.str_param(codec, "codec")

    class AvroApacheAvro:
        @public
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
        @public
        def __init__(self, compression_type: Optional[str] = None):
            self.compression_type = check.opt_str_param(compression_type, "compression_type")

    class CSVCommaSeparatedValues:
        @public
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
        @public
        def __init__(
            self,
            format_type: str,
            compression: Union["R2Destination.NoCompression", "R2Destination.GZIP"],
        ):
            self.format_type = check.str_param(format_type, "format_type")
            self.compression = check.inst_param(
                compression, "compression", (R2Destination.NoCompression, R2Destination.GZIP)
            )

    @public
    def __init__(
        self,
        name: str,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        s3_bucket_name: str,
        s3_bucket_path: str,
        format: Union[
            "R2Destination.AvroApacheAvro",
            "R2Destination.CSVCommaSeparatedValues",
            "R2Destination.JSONLinesNewlineDelimitedJSON",
        ],
        s3_path_format: Optional[str] = None,
        file_name_pattern: Optional[str] = None,
    ):
        """Airbyte Destination for R2.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/r2

        Args:
            name (str): The name of the destination.
            account_id (str): Cloudflare account ID
            access_key_id (str): The access key ID to access the R2 bucket. Airbyte requires Read and Write permissions to the given bucket. Read more here.
            secret_access_key (str): The corresponding secret to the access key ID. Read more here
            s3_bucket_name (str): The name of the R2 bucket. Read more here.
            s3_bucket_path (str): Directory under the R2 bucket where data will be written.
            format (Union[R2Destination.AvroApacheAvro, R2Destination.CSVCommaSeparatedValues, R2Destination.JSONLinesNewlineDelimitedJSON]): Format of the data output. See here for more details
            s3_path_format (Optional[str]): Format string on how data will be organized inside the R2 bucket directory. Read more here
            file_name_pattern (Optional[str]): The pattern allows you to set the file-name format for the R2 staging file(s)
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
    @public
    def __init__(
        self,
        name: str,
        username: str,
        jdbc_url: str,
        password: Optional[str] = None,
        schema: Optional[str] = None,
    ):
        """Airbyte Destination for Jdbc.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/postgres

        Args:
            name (str): The name of the destination.
            username (str): The username which is used to access the database.
            password (Optional[str]): The password associated with this username.
            jdbc_url (str): JDBC formatted url. See the standard here.
            schema (Optional[str]): If you leave the schema unspecified, JDBC defaults to a schema named "public".
        """
        self.username = check.str_param(username, "username")
        self.password = check.opt_str_param(password, "password")
        self.jdbc_url = check.str_param(jdbc_url, "jdbc_url")
        self.schema = check.opt_str_param(schema, "schema")
        super().__init__("Jdbc", name)


class KeenDestination(GeneratedAirbyteDestination):
    @public
    def __init__(
        self, name: str, project_id: str, api_key: str, infer_timestamp: Optional[bool] = None
    ):
        """Airbyte Destination for Keen.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/keen

        Args:
            name (str): The name of the destination.
            project_id (str): To get Keen Project ID, navigate to the Access tab from the left-hand, side panel and check the Project Details section.
            api_key (str): To get Keen Master API Key, navigate to the Access tab from the left-hand, side panel and check the Project Details section.
            infer_timestamp (Optional[bool]): Allow connector to guess keen.timestamp value based on the streamed data.
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.api_key = check.str_param(api_key, "api_key")
        self.infer_timestamp = check.opt_bool_param(infer_timestamp, "infer_timestamp")
        super().__init__("Keen", name)


class TidbDestination(GeneratedAirbyteDestination):
    @public
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
        """Airbyte Destination for Tidb.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/tidb

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            ssl (Optional[bool]): Encrypt data using SSL.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
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
    @public
    def __init__(self, name: str, project_id: str, credentials_json: Optional[str] = None):
        """Airbyte Destination for Firestore.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/firestore

        Args:
            name (str): The name of the destination.
            project_id (str): The GCP project ID for the project containing the target BigQuery dataset.
            credentials_json (Optional[str]): The contents of the JSON service account key. Check out the docs if you need help generating this key. Default credentials will be used if this field is left empty.
        """
        self.project_id = check.str_param(project_id, "project_id")
        self.credentials_json = check.opt_str_param(credentials_json, "credentials_json")
        super().__init__("Firestore", name)


class ScyllaDestination(GeneratedAirbyteDestination):
    @public
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
        """Airbyte Destination for Scylla.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/scylla

        Args:
            name (str): The name of the destination.
            keyspace (str): Default Scylla keyspace to create data in.
            username (str): Username to use to access Scylla.
            password (str): Password associated with Scylla.
            address (str): Address to connect to.
            port (int): Port of Scylla.
            replication (Optional[int]): Indicates to how many nodes the data should be replicated to.
        """
        self.keyspace = check.str_param(keyspace, "keyspace")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.address = check.str_param(address, "address")
        self.port = check.int_param(port, "port")
        self.replication = check.opt_int_param(replication, "replication")
        super().__init__("Scylla", name)


class RedisDestination(GeneratedAirbyteDestination):
    @public
    def __init__(
        self, name: str, host: str, port: int, username: str, password: str, cache_type: str
    ):
        """Airbyte Destination for Redis.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redis

        Args:
            name (str): The name of the destination.
            host (str): Redis host to connect to.
            port (int): Port of Redis.
            username (str): Username associated with Redis.
            password (str): Password associated with Redis.
            cache_type (str): Redis cache type to store data in.
        """
        self.host = check.str_param(host, "host")
        self.port = check.int_param(port, "port")
        self.username = check.str_param(username, "username")
        self.password = check.str_param(password, "password")
        self.cache_type = check.str_param(cache_type, "cache_type")
        super().__init__("Redis", name)


class MqttDestination(GeneratedAirbyteDestination):
    @public
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
        """Airbyte Destination for Mqtt.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/mqtt

        Args:
            name (str): The name of the destination.
            broker_host (str): Host of the broker to connect to.
            broker_port (int): Port of the broker.
            use_tls (bool): Whether to use TLS encryption on the connection.
            username (Optional[str]): User name to use for the connection.
            password (Optional[str]): Password to use for the connection.
            topic_pattern (str): Topic pattern in which the records will be sent. You can use patterns like '{namespace}' and/or '{stream}' to send the message to a specific topic based on these values. Notice that the topic name will be transformed to a standard naming convention.
            topic_test (Optional[str]): Topic to test if Airbyte can produce messages.
            client (Optional[str]): A client identifier that is unique on the server being connected to.
            publisher_sync (bool): Wait synchronously until the record has been sent to the broker.
            connect_timeout (int):  Maximum time interval (in seconds) the client will wait for the network connection to the MQTT server to be established.
            automatic_reconnect (bool): Whether the client will automatically attempt to reconnect to the server if the connection is lost.
            clean_session (bool): Whether the client and server should remember state across restarts and reconnects.
            message_retained (bool): Whether or not the publish message should be retained by the messaging engine.
            message_qos (str): Quality of service used for each message to be delivered.
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
        @public
        def __init__(
            self,
        ):
            self.method = "Standard"

    class NoEncryption:
        @public
        def __init__(
            self,
        ):
            self.encryption_type = "none"

    class AESCBCEnvelopeEncryption:
        @public
        def __init__(self, key_encrypting_key: Optional[str] = None):
            self.encryption_type = "aes_cbc_envelope"
            self.key_encrypting_key = check.opt_str_param(key_encrypting_key, "key_encrypting_key")

    class S3Staging:
        @public
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

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        schema: str,
        uploading_method: Union["RedshiftDestination.Standard", "RedshiftDestination.S3Staging"],
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Destination for Redshift.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/redshift

        Args:
            name (str): The name of the destination.
            host (str): Host Endpoint of the Redshift Cluster (must include the cluster-id, region and end with .redshift.amazonaws.com)
            port (int): Port of the database.
            username (str): Username to use to access the database.
            password (str): Password associated with the username.
            database (str): Name of the database.
            schema (str): The default schema tables are written to if the source does not specify a namespace. Unless specifically configured, the usual value for this field is "public".
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
            uploading_method (Union[RedshiftDestination.Standard, RedshiftDestination.S3Staging]): The method how the data will be uploaded to the database.
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
    @public
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
        """Airbyte Destination for Pulsar.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/pulsar

        Args:
            name (str): The name of the destination.
            brokers (str): A list of host/port pairs to use for establishing the initial connection to the Pulsar cluster.
            use_tls (bool): Whether to use TLS encryption on the connection.
            topic_type (str): It identifies type of topic. Pulsar supports two kind of topics: persistent and non-persistent. In persistent topic, all messages are durably persisted on disk (that means on multiple disks unless the broker is standalone), whereas non-persistent topic does not persist message into storage disk.
            topic_tenant (str): The topic tenant within the instance. Tenants are essential to multi-tenancy in Pulsar, and spread across clusters.
            topic_namespace (str): The administrative unit of the topic, which acts as a grouping mechanism for related topics. Most topic configuration is performed at the namespace level. Each tenant has one or multiple namespaces.
            topic_pattern (str): Topic pattern in which the records will be sent. You can use patterns like '{namespace}' and/or '{stream}' to send the message to a specific topic based on these values. Notice that the topic name will be transformed to a standard naming convention.
            topic_test (Optional[str]): Topic to test if Airbyte can produce messages.
            producer_name (Optional[str]): Name for the producer. If not filled, the system will generate a globally unique name which can be accessed with.
            producer_sync (Optional[bool]): Wait synchronously until the record has been sent to Pulsar.
            compression_type (str): Compression type for the producer.
            send_timeout_ms (int): If a message is not acknowledged by a server before the send-timeout expires, an error occurs (in ms).
            max_pending_messages (int): The maximum size of a queue holding pending messages.
            max_pending_messages_across_partitions (int): The maximum number of pending messages across partitions.
            batching_enabled (bool): Control whether automatic batching of messages is enabled for the producer.
            batching_max_messages (int): Maximum number of messages permitted in a batch.
            batching_max_publish_delay (int):  Time period in milliseconds within which the messages sent will be batched.
            block_if_queue_full (bool): If the send operation should block when the outgoing message queue is full.
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
        @public
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
        @public
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
        @public
        def __init__(self, password: str):
            self.password = check.str_param(password, "password")

    class SelectAnotherOption:
        @public
        def __init__(self, method: str):
            self.method = check.str_param(method, "method")

    class RecommendedInternalStaging:
        @public
        def __init__(self, method: str):
            self.method = check.str_param(method, "method")

    class NoEncryption:
        @public
        def __init__(
            self,
        ):
            self.encryption_type = "none"

    class AESCBCEnvelopeEncryption:
        @public
        def __init__(self, key_encrypting_key: Optional[str] = None):
            self.encryption_type = "aes_cbc_envelope"
            self.key_encrypting_key = check.opt_str_param(key_encrypting_key, "key_encrypting_key")

    class AWSS3Staging:
        @public
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
        @public
        def __init__(self, method: str, project_id: str, bucket_name: str, credentials_json: str):
            self.method = check.str_param(method, "method")
            self.project_id = check.str_param(project_id, "project_id")
            self.bucket_name = check.str_param(bucket_name, "bucket_name")
            self.credentials_json = check.str_param(credentials_json, "credentials_json")

    class AzureBlobStorageStaging:
        @public
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

    @public
    def __init__(
        self,
        name: str,
        host: str,
        role: str,
        warehouse: str,
        database: str,
        schema: str,
        username: str,
        credentials: Union[
            "SnowflakeDestination.OAuth20",
            "SnowflakeDestination.KeyPairAuthentication",
            "SnowflakeDestination.UsernameAndPassword",
        ],
        loading_method: Union[
            "SnowflakeDestination.SelectAnotherOption",
            "SnowflakeDestination.RecommendedInternalStaging",
            "SnowflakeDestination.AWSS3Staging",
            "SnowflakeDestination.GoogleCloudStorageStaging",
            "SnowflakeDestination.AzureBlobStorageStaging",
        ],
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Destination for Snowflake.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/snowflake

        Args:
            name (str): The name of the destination.
            host (str): Enter your Snowflake account's locator (in the format ...snowflakecomputing.com)
            role (str): Enter the role that you want to use to access Snowflake
            warehouse (str): Enter the name of the warehouse that you want to sync data into
            database (str): Enter the name of the database you want to sync data into
            schema (str): Enter the name of the default schema
            username (str): Enter the name of the user you want to use to access the database
            jdbc_url_params (Optional[str]): Enter the additional properties to pass to the JDBC URL string when connecting to the database (formatted as key=value pairs separated by the symbol &). Example: key1=value1&key2=value2&key3=value3
            loading_method (Union[SnowflakeDestination.SelectAnotherOption, SnowflakeDestination.RecommendedInternalStaging, SnowflakeDestination.AWSS3Staging, SnowflakeDestination.GoogleCloudStorageStaging, SnowflakeDestination.AzureBlobStorageStaging]): Select a data staging method
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
        @public
        def __init__(
            self,
        ):
            self.mode = "disable"

    class Allow:
        @public
        def __init__(
            self,
        ):
            self.mode = "allow"

    class Prefer:
        @public
        def __init__(
            self,
        ):
            self.mode = "prefer"

    class Require:
        @public
        def __init__(
            self,
        ):
            self.mode = "require"

    class VerifyCa:
        @public
        def __init__(self, ca_certificate: str, client_key_password: Optional[str] = None):
            self.mode = "verify-ca"
            self.ca_certificate = check.str_param(ca_certificate, "ca_certificate")
            self.client_key_password = check.opt_str_param(
                client_key_password, "client_key_password"
            )

    class VerifyFull:
        @public
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

    @public
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        database: str,
        schema: str,
        username: str,
        ssl_mode: Union[
            "PostgresDestination.Disable",
            "PostgresDestination.Allow",
            "PostgresDestination.Prefer",
            "PostgresDestination.Require",
            "PostgresDestination.VerifyCa",
            "PostgresDestination.VerifyFull",
        ],
        password: Optional[str] = None,
        ssl: Optional[bool] = None,
        jdbc_url_params: Optional[str] = None,
    ):
        """Airbyte Destination for Postgres.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/postgres

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the database.
            port (int): Port of the database.
            database (str): Name of the database.
            schema (str): The default schema tables are written to if the source does not specify a namespace. The usual value for this field is "public".
            username (str): Username to use to access the database.
            password (Optional[str]): Password associated with the username.
            ssl (Optional[bool]): Encrypt data using SSL. When activating SSL, please select one of the connection modes.
            ssl_mode (Union[PostgresDestination.Disable, PostgresDestination.Allow, PostgresDestination.Prefer, PostgresDestination.Require, PostgresDestination.VerifyCa, PostgresDestination.VerifyFull]): SSL connection modes.   disable - Chose this mode to disable encryption of communication between Airbyte and destination database  allow - Chose this mode to enable encryption only when required by the source database  prefer - Chose this mode to allow unencrypted connection only if the source database does not support encryption  require - Chose this mode to always require encryption. If the source database server does not support encryption, connection will fail   verify-ca - Chose this mode to always require encryption and to verify that the source database server has a valid SSL certificate   verify-full - This is the most secure mode. Chose this mode to always require encryption and to verify the identity of the source database server  See more information -  in the docs.
            jdbc_url_params (Optional[str]): Additional properties to pass to the JDBC URL string when connecting to the database formatted as 'key=value' pairs separated by the symbol '&'. (example: key1=value1&key2=value2&key3=value3).
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
    @public
    def __init__(self, name: str, TODO: Optional[str] = None):
        """Airbyte Destination for Scaffold Destination Python.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/scaffold-destination-python

        Args:
            name (str): The name of the destination.
            TODO (Optional[str]): FIX ME
        """
        self.TODO = check.opt_str_param(TODO, "TODO")
        super().__init__("Scaffold Destination Python", name)


class LocalJsonDestination(GeneratedAirbyteDestination):
    @public
    def __init__(self, name: str, destination_path: str):
        """Airbyte Destination for Local Json.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/local-json

        Args:
            name (str): The name of the destination.
            destination_path (str): Path to the directory where json files will be written. The files will be placed inside that local mount. For more information check out our docs
        """
        self.destination_path = check.str_param(destination_path, "destination_path")
        super().__init__("Local Json", name)


class MeilisearchDestination(GeneratedAirbyteDestination):
    @public
    def __init__(self, name: str, host: str, api_key: Optional[str] = None):
        """Airbyte Destination for Meilisearch.

        Documentation can be found at https://docs.airbyte.com/integrations/destinations/meilisearch

        Args:
            name (str): The name of the destination.
            host (str): Hostname of the MeiliSearch instance.
            api_key (Optional[str]): MeiliSearch API Key. See the docs for more information on how to obtain this key.
        """
        self.host = check.str_param(host, "host")
        self.api_key = check.opt_str_param(api_key, "api_key")
        super().__init__("Meilisearch", name)
