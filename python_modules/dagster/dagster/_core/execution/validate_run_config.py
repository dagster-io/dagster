from typing import Any, Mapping, Optional, Union

import dagster._check as check
from dagster._core.definitions import JobDefinition
from dagster._core.definitions.run_config import RunConfig, convert_config_input
from dagster._core.system_config.objects import ResolvedRunConfig


def validate_run_config(
    job_def: JobDefinition,
    run_config: Optional[Union[Mapping[str, Any], RunConfig]] = None,
) -> Mapping[str, Any]:
    """Function to validate a provided run config blob against a given job.

    If validation is successful, this function will return a dictionary representation of the
    validated config actually used during execution.

    Args:
        job_def (JobDefinition): The job definition to validate run
            config against
        run_config (Optional[Dict[str, Any]]): The run config to validate

    Returns:
        Dict[str, Any]: A dictionary representation of the validated config.
    """
    check.inst_param(job_def, "job_def", JobDefinition)
    run_config = check.opt_mapping_param(
        convert_config_input(run_config), "run_config", key_type=str
    )

    return ResolvedRunConfig.build(job_def, run_config).to_dict()
