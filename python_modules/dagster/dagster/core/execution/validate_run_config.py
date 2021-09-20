from typing import Any, Dict, Optional

from dagster import check
from dagster.core.definitions import PipelineDefinition
from dagster.core.system_config.objects import ResolvedRunConfig


def validate_run_config(
    pipeline_def: PipelineDefinition,
    run_config: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Function to validate a provided run config blob against a given pipeline and mode.

    If validation is successful, this function will return a dictionary representation of the
    validated config actually used during execution.

    Args:
        pipeline_def (PipelineDefinition): The pipeline definition to validate run config against
        run_config (Optional[Dict[str, Any]]): The run config to validate
        mode (str): The mode of the pipeline to validate against (different modes may require
            different config)

    Returns:
        Dict[str, Any]: A dictionary representation of the validated config.
    """

    pipeline_def = check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    run_config = check.opt_dict_param(run_config, "run_config", key_type=str)
    mode = check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name())

    return ResolvedRunConfig.build(pipeline_def, run_config, mode=mode).to_dict()
