# Keys used to pass the dlt source, pipeline, and translator from asset definition to execution
# via the asset spec metadata. These are live objects and are not JSON serializable.
META_KEY_SOURCE = "dagster-dlt/dlt_source"
META_KEY_PIPELINE = "dagster-dlt/dlt_pipeline"
META_KEY_TRANSLATOR = "dagster-dlt/dagster_dlt_translator"
