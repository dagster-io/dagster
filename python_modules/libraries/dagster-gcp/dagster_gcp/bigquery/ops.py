import hashlib

from dagster import (
    In,
    List,
    Nothing,
    Out,
    _check as check,
    op,
)
from dagster_pandas import DataFrame
from google.cloud.bigquery.encryption_configuration import EncryptionConfiguration
from google.cloud.bigquery.job import LoadJobConfig, QueryJobConfig
from google.cloud.bigquery.table import TimePartitioning

from .configs import (
    define_bigquery_create_dataset_config,
    define_bigquery_delete_dataset_config,
    define_bigquery_load_config,
    define_bigquery_query_config,
)
from .types import BigQueryLoadSource

_START = "start"


def _preprocess_config(cfg):
    destination_encryption_configuration = cfg.get("destination_encryption_configuration")
    time_partitioning = cfg.get("time_partitioning")

    if destination_encryption_configuration is not None:
        cfg["destination_encryption_configuration"] = EncryptionConfiguration(
            kms_key_name=destination_encryption_configuration
        )

    if time_partitioning is not None:
        cfg["time_partitioning"] = TimePartitioning(**time_partitioning)

    return cfg


def bq_op_for_queries(sql_queries):
    """Executes BigQuery SQL queries.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    """
    sql_queries = check.list_param(sql_queries, "sql queries", of_type=str)
    m = hashlib.sha1()
    for query in sql_queries:
        m.update(query.encode("utf-8"))
    hash_str = m.hexdigest()[:10]
    name = f"bq_op_{hash_str}"

    @op(
        name=name,
        ins={_START: In(Nothing)},
        out=Out(List[DataFrame]),
        config_schema=define_bigquery_query_config(),
        required_resource_keys={"bigquery"},
        tags={"kind": "sql", "sql": "\n".join(sql_queries)},
    )
    def _bq_fn(context):
        query_job_config = _preprocess_config(context.op_config.get("query_job_config", {}))

        # Retrieve results as pandas DataFrames
        results = []
        for sql_query in sql_queries:
            # We need to construct a new QueryJobConfig for each query.
            # See: https://bit.ly/2VjD6sl
            cfg = QueryJobConfig(**query_job_config) if query_job_config else None
            context.log.info(
                "executing query %s with config: %s"
                % (sql_query, cfg.to_api_repr() if cfg else "(no config provided)")
            )
            results.append(
                context.resources.bigquery.query(sql_query, job_config=cfg).to_dataframe()
            )

        return results

    return _bq_fn


BIGQUERY_LOAD_CONFIG = define_bigquery_load_config()


@op(
    ins={"paths": In(List[str])},
    out=Out(Nothing),
    config_schema=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={"bigquery"},
)
def import_gcs_paths_to_bq(context, paths):
    return _execute_load_in_source(context, paths, BigQueryLoadSource.GCS)


@op(
    ins={"df": In(DataFrame)},
    out=Out(Nothing),
    config_schema=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={"bigquery"},
)
def import_df_to_bq(context, df):
    return _execute_load_in_source(context, df, BigQueryLoadSource.DataFrame)


@op(
    ins={"path": In(str)},
    out=Out(Nothing),
    config_schema=BIGQUERY_LOAD_CONFIG,
    required_resource_keys={"bigquery"},
)
def import_file_to_bq(context, path):
    return _execute_load_in_source(context, path, BigQueryLoadSource.File)


def _execute_load_in_source(context, source, source_name):
    destination = context.op_config.get("destination")
    load_job_config = _preprocess_config(context.op_config.get("load_job_config", {}))
    cfg = LoadJobConfig(**load_job_config) if load_job_config else None

    context.log.info(
        "executing BQ load with config: %s for source %s"
        % (cfg.to_api_repr() if cfg else "(no config provided)", source)
    )

    if source_name == BigQueryLoadSource.DataFrame:
        context.resources.bigquery.load_table_from_dataframe(
            source, destination, job_config=cfg
        ).result()

    # Load from file. See: https://cloud.google.com/bigquery/docs/loading-data-local
    elif source_name == BigQueryLoadSource.File:
        with open(source, "rb") as file_obj:
            context.resources.bigquery.load_table_from_file(
                file_obj, destination, job_config=cfg
            ).result()

    # Load from GCS. See: https://cloud.google.com/bigquery/docs/loading-data-cloud-storage
    elif source_name == BigQueryLoadSource.GCS:
        context.resources.bigquery.load_table_from_uri(source, destination, job_config=cfg).result()


@op(
    ins={_START: In(Nothing)},
    config_schema=define_bigquery_create_dataset_config(),
    required_resource_keys={"bigquery"},
)
def bq_create_dataset(context):
    """BigQuery Create Dataset.

    This op encapsulates creating a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    """
    (dataset, exists_ok) = [context.op_config.get(k) for k in ("dataset", "exists_ok")]
    context.log.info("executing BQ create_dataset for dataset %s" % (dataset))
    context.resources.bigquery.create_dataset(dataset, exists_ok)


@op(
    ins={_START: In(Nothing)},
    config_schema=define_bigquery_delete_dataset_config(),
    required_resource_keys={"bigquery"},
)
def bq_delete_dataset(context):
    """BigQuery Delete Dataset.

    This op encapsulates deleting a BigQuery dataset.

    Expects a BQ client to be provisioned in resources as context.resources.bigquery.
    """
    (dataset, delete_contents, not_found_ok) = [
        context.op_config.get(k) for k in ("dataset", "delete_contents", "not_found_ok")
    ]

    context.log.info("executing BQ delete_dataset for dataset %s" % dataset)

    context.resources.bigquery.delete_dataset(
        dataset, delete_contents=delete_contents, not_found_ok=not_found_ok
    )
