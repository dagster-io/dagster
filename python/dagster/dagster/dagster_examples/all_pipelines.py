import dagster.embedded_cli
import dagster_examples.dagster_examples.pandas_hello_world.pipeline
import dagster_examples.dagster_examples.qhp.pipeline
import dagster_examples.dagster_examples.sql_hello_world.pipeline

if __name__ == '__main__':
    import sys
    dagster.embedded_cli.embedded_dagster_multi_pipeline_cli_main(
        sys.argv, [
            dagster_examples.pandas_hello_world.pipeline.define_pipeline(),
            dagster_examples.qhp.pipeline.define_pipeline(),
            dagster_examples.sql_hello_world.pipeline.define_pipeline(),
        ]
    )
