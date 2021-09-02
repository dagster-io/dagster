from dagster import execute_pipeline
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.test_utils import instance_for_test
from dagster_test.toys.graph_job_repos import graph_job_dev_repo, graph_job_prod_repo


def test_dev_pipelines():
    with instance_for_test() as instance:
        recon_repo = ReconstructableRepository.for_file(__file__, "graph_job_dev_repo")
        dev_pipelines = graph_job_dev_repo.get_all_pipelines()
        assert len(dev_pipelines) == 5
        for pipeline in dev_pipelines:
            execute_pipeline(
                recon_repo.get_reconstructable_pipeline(pipeline.name),
                instance=instance,
            )


def test_prod_pipelines():
    with instance_for_test() as instance:
        recon_repo = ReconstructableRepository.for_file(__file__, "graph_job_prod_repo")
        prod_pipelines = graph_job_prod_repo.get_all_pipelines()
        assert len(prod_pipelines) == 8
        for pipeline in prod_pipelines:
            if pipeline.name == "process_customer_data_dump":
                run_config = {"solids": {"process_customer": {"config": {"customer_id": "abc123"}}}}
            else:
                run_config = None
            execute_pipeline(
                recon_repo.get_reconstructable_pipeline(pipeline.name),
                run_config=run_config,
                instance=instance,
            )
