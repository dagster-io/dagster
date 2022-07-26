from typing import Any, Mapping, Optional, cast

import dagster._check as check
from dagster._core.definitions import JobDefinition, PipelineDefinition
from dagster._core.system_config.objects import ResolvedRunConfig


def validate_run_config(
    job_def: Optional[JobDefinition] = None,
    run_config: Optional[Mapping[str, Any]] = None,
    mode: Optional[str] = None,
    pipeline_def: Optional[PipelineDefinition] = None,
) -> Mapping[str, Any]:
    """Function to validate a provided run config blob against a given job. For legacy APIs, a
    pipeline/mode can also be passed in.

    If validation is successful, this function will return a dictionary representation of the
    validated config actually used during execution.

    Args:
        job_def (Union[PipelineDefinition, JobDefinition]): The job definition to validate run
            config against
        run_config (Optional[Dict[str, Any]]): The run config to validate
        mode (str): The mode of the pipeline to validate against (different modes may require
            different config)
        pipeline_def (PipelineDefinition): The pipeline definition to validate run config against.

    Returns:
        Dict[str, Any]: A dictionary representation of the validated config.
    """

    job_def = check.opt_inst_param(job_def, "job_def", (JobDefinition, PipelineDefinition))
    pipeline_def = check.opt_inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    run_config = check.opt_mapping_param(run_config, "run_config", key_type=str)

    if job_def and pipeline_def:
        check.failed("Cannot specify both a job_def and a pipeline_def")

    pipeline_or_job_def = pipeline_def or job_def

    if pipeline_or_job_def is None:
        check.failed("Must specify at least one of job_def and pipeline_def")

    pipeline_or_job_def = cast(PipelineDefinition, pipeline_def or job_def)
    mode = check.opt_str_param(mode, "mode", default=pipeline_or_job_def.get_default_mode_name())

    return ResolvedRunConfig.build(pipeline_or_job_def, run_config, mode=mode).to_dict()
