from dagster import StaticPartitionsDefinition

docs_partitions_def = StaticPartitionsDefinition(
    ["concepts", "dagster-cloud", "deployment", "guides", "integrations"]
)
