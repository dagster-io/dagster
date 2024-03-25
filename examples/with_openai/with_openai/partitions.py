from dagster import StaticPartitionsDefinition

docs_partitions_def = StaticPartitionsDefinition(["guides", "integrations"])
