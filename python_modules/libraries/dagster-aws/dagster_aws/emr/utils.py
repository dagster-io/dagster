import copy

from dagster import check


def subset_environment_dict(environment_dict, solid_name):
    '''Drops solid config for solids other than solid_name; this subsetting is required when
    executing a single solid on EMR to pass config validation.
    '''
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(solid_name, 'solid_name')

    subset = copy.deepcopy(environment_dict)
    if 'solids' in subset:
        solid_config_keys = list(subset['solids'].keys())
        for key in solid_config_keys:
            if key != solid_name:
                del subset['solids'][key]
    return subset
