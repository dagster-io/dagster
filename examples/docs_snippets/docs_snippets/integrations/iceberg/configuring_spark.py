from dagster_iceberg.io_manager.spark import SparkIcebergIOManager

SPARK_CONFIG = {
    "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.postgres": "org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.postgres.type": "jdbc",
    "spark.sql.catalog.postgres.uri": "jdbc:postgresql://postgres:5432/test",
    "spark.sql.catalog.postgres.jdbc.user": "test",
    "spark.sql.catalog.postgres.jdbc.password": "test",
    "spark.sql.catalog.postgres.warehouse": "/home/iceberg/warehouse",
    "spark.sql.defaultCatalog": "postgres",
    "spark.eventLog.enabled": "true",
    "spark.eventLog.dir": "/home/iceberg/spark-events",
    "spark.history.fs.logDirectory": "/home/iceberg/spark-events",
    "spark.sql.catalogImplementation": "in-memory",
    "spark.sql.execution.arrow.pyspark.enabled": "true",
}

io_manager = SparkIcebergIOManager(
    catalog_name="test",
    namespace="dagster",
    spark_config=SPARK_CONFIG,
    remote_url="sc://localhost",
)
