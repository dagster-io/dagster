from typing import Mapping
from dagster._config.evaluate_value_result import EvaluateValueResult


def process_config(
    config_type: object, config_dict: Mapping[str, object]
) -> EvaluateValueResult[Mapping]:
    config_type = normalize_config_type(config_type)
    validate_evr = validate_config(config_type, config_dict)
    if not validate_evr.success:
        return validate_evr

    return post_process_config(config_type, validate_evr.value)
