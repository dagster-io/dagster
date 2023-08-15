import copy

import dagster._check as check


def subset_run_config(run_config, op_name):
    """Drops op config for ops other than solid_name; this subsetting is required when
    executing a single op on EMR to pass config validation.
    """
    check.dict_param(run_config, "run_config")
    check.str_param(op_name, "solid_name")

    subset = copy.deepcopy(run_config)
    if "ops" in subset:
        solid_config_keys = list(subset["ops"].keys())
        for key in solid_config_keys:
            if key != op_name:
                del subset["ops"][key]
    return subset
