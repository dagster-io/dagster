from dagster.core.execution.api import create_execution_plan


def test_load_pipeline():
    from docs_snippets.overview.modes_resources.pipeline_with_modes import generate_tables_pipeline

    create_execution_plan(generate_tables_pipeline, mode="local_dev")
    create_execution_plan(
        generate_tables_pipeline,
        mode="prod",
        run_config={
            "resources": {
                "database": {
                    "config": {
                        "hostname": "some_hostname",
                        "port": 5423,
                        "username": "someone",
                        "password": "verysecret",
                        "db_name": "prod_db",
                    }
                }
            }
        },
    )
