from dagster import execute_pipeline
from dagster_test.toys.graph_job_repos import dev_repo, prod_repo


def test_dev_pipelines():
    dev_pipelines = dev_repo.get_all_pipelines()
    assert len(dev_pipelines) == 4
    for pipeline in dev_pipelines:
        execute_pipeline(pipeline)


def test_prod_pipelines():
    prod_pipelines = prod_repo.get_all_pipelines()
    assert len(prod_pipelines) == 5
    for pipeline in prod_pipelines:
        if pipeline.name == "process_customer_data_dump":
            run_config = {"solids": {"process_customer": {"config": {"customer_id": "abc123"}}}}
        else:
            run_config = None
        execute_pipeline(pipeline, run_config=run_config)
