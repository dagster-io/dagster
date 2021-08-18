from dagster_airflow.factory import make_airflow_dag

dag, steps = make_airflow_dag(
    module_name="docs_snippets_crag.intro_tutorial.airflow",
    pipeline_name="hello_cereal_pipeline",
    run_config={"storage": {"filesystem": {"config": {"base_dir": "/container_tmp"}}}},
    dag_id=None,
    dag_description=None,
    dag_kwargs=None,
    op_kwargs={"host_tmp_dir": "/host_tmp", "tmp_dir": "/container_tmp"},
)
