from dagster_airflow.factory import make_airflow_dag_containerized

dag, steps = make_airflow_dag_containerized(
    module_name="docs_snippets_crag.intro_tutorial.airflow",
    pipeline_name="hello_cereal_pipeline",
    image="dagster-airflow-demo-repository",
    run_config={"storage": {"filesystem": {"config": {"base_dir": "/tmp"}}}},
    dag_id=None,
    dag_description=None,
    dag_kwargs=None,
    op_kwargs=None,
)
