from dagster import build_schedule_context, execute_pipeline
from docs_snippets.guides.dagster.graph_job_op import (
    graph_job_test,
    graph_with_config,
    graph_with_config_and_schedule,
    graph_with_config_mapping,
    graph_with_resources,
    graph_with_schedule,
    op_in_out,
    op_multi_out,
    pipeline_mode_test,
    pipeline_with_preset_and_schedule,
    pipeline_with_resources,
    pipeline_with_schedule,
    prod_dev_jobs,
    prod_dev_modes,
    simple_graph,
    simple_pipeline,
    solid_input_output_def,
)

jobs = [
    (simple_graph, "do_it_all"),
    (graph_with_resources, "do_it_all_job"),
    (graph_with_config, "do_it_all_job"),
    (graph_job_test, "do_it_all_job"),
]
job_repos = [
    (prod_dev_jobs, "prod_repo"),
    (prod_dev_jobs, "dev_repo"),
]
functions = [
    (graph_with_config_mapping, "execute_do_it_all"),
    (graph_job_test, "test_do_it_all"),
    (pipeline_mode_test, "test_do_it_all"),
]
job_schedules = [
    (graph_with_schedule, "do_it_all_schedule"),
    (graph_with_config_and_schedule, "do_it_all_schedule"),
]
pipelines = [
    (simple_pipeline, "do_it_all"),
    (pipeline_mode_test, "do_it_all"),
    (prod_dev_modes, "do_it_all"),
    (pipeline_with_resources, "do_it_all"),
    (pipeline_with_schedule, "do_it_all"),
    (pipeline_with_preset_and_schedule, "do_it_all"),
]
ops_and_solids = [
    (solid_input_output_def, "do_something"),
    (op_in_out, "do_something"),
    (op_multi_out, "do_something"),
]


def test_jobs():
    for module, attr_name in jobs:
        job = getattr(module, attr_name)
        try:
            assert job.execute_in_process().success
        except Exception as ex:
            raise Exception(
                f"Error while executing job '{job.name}' from module '{module.__name__}'"
            ) from ex


def test_pipelines():
    for module, attr_name in pipelines:
        pipeline = getattr(module, attr_name)
        try:
            if pipeline.preset_defs:
                for preset in pipeline.preset_defs:
                    assert execute_pipeline(pipeline, preset=preset.name).success
            else:
                for mode in pipeline.mode_definitions:
                    assert execute_pipeline(pipeline, mode=mode.name).success
        except Exception as ex:
            raise Exception(
                f"Error while executing pipeline '{pipeline.name}' from module '{module.__name__}'"
            ) from ex


def test_functions():
    try:
        for module, attr_name in functions:
            fn = getattr(module, attr_name)
            fn()
    except Exception as ex:
        raise Exception(
            f"Error while executing function '{fn.__name__}' from module '{module.__name__}'"
        ) from ex


def test_job_schedules():
    for module, attr_name in job_schedules:
        schedule = getattr(module, attr_name)
        try:
            assert schedule.has_loadable_target()
            job = schedule.load_target()
            context = build_schedule_context()
            run_config = schedule.evaluate_tick(context).run_requests[0].run_config
            assert job.execute_in_process(run_config=run_config).success
        except Exception as ex:
            raise Exception(
                f"Error while executing schedule '{schedule.name}' from module '{module.__name__}'"
            ) from ex


def test_ops():
    for module, attr_name in ops_and_solids:
        op_or_solid = getattr(module, attr_name)
        try:
            assert op_or_solid("5")
        except Exception as ex:
            raise Exception(
                f"Error while executing op or solid '{op_or_solid.name}' from module '{module.__name__}'"
            ) from ex
