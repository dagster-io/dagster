import copy

from dagster import check


def _dict_merge(from_dict, onto_dict):
    check.dict_param(from_dict, 'from_dict')
    check.dict_param(onto_dict, 'onto_dict')

    for from_key, from_value in from_dict.items():
        if from_key not in onto_dict:
            onto_dict[from_key] = from_value
        else:
            onto_value = onto_dict[from_key]

            if isinstance(from_value, dict) and isinstance(onto_value, dict):
                onto_dict[from_key] = _dict_merge(from_value, onto_value)
            else:
                onto_dict[from_key] = from_value  # smash

    return onto_dict


def dict_merge(from_dict, onto_dict):
    onto_dict = copy.deepcopy(onto_dict)
    return _dict_merge(from_dict, onto_dict)
