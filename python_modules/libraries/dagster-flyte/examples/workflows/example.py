from dagster_flyte import compile_pipeline_to_flyte  # pylint: disable=import-error

from dagster import pipeline, solid


@solid
def mult_x(_, x: int) -> int:
    return 2 * x


@pipeline
def pipe():
    mult_x()


run_config: dict = {
    "storage": {"filesystem": {}},
    "solids": {"mult_x": {"inputs": {"x": {"value": 2}}}},
}

compute_dict = {
    "mult_x": {
        "storage_request": "300Mi",
        "memory_request": "300Mi",
        "cpu_request": "200m",
        "storage_limit": "300Mi",
        "memory_limit": "300Mi",
        "cpu_limit": "200m",
    }
}

workflow_obj = compile_pipeline_to_flyte(
    pipe, run_config=run_config, compute_dict=compute_dict, module=__name__
)
