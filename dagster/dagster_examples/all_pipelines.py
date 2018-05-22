import dagster.cli.embedded_cli
import dagster.dagster_examples.pandas_hello_world.pipeline
import dagster.dagster_examples.qhp.pipeline
import dagster.dagster_examples.sql_hello_world.pipeline

if __name__ == '__main__':
    import sys
    dagster.cli.embedded_cli.embedded_dagster_multi_pipeline_cli_main(
        sys.argv, [
            dagster.dagster_examples.pandas_hello_world.pipeline.define_pipeline(),
            dagster.dagster_examples.qhp.pipeline.define_pipeline(),
            dagster.dagster_examples.sql_hello_world.pipeline.define_pipeline(),
        ]
    )
