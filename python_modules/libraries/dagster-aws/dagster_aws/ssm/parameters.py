from typing import Any, Dict, List, Optional, Sequence

import boto3.session
import dagster._check as check

from dagster_aws.utils import construct_boto_client_retry_config


def construct_ssm_client(
    max_attempts: int, region_name: Optional[str] = None, profile_name: Optional[str] = None
):
    check.int_param(max_attempts, "max_attempts")
    check.opt_str_param(region_name, "region_name")
    check.opt_str_param(profile_name, "profile_name")

    client_session = boto3.session.Session(profile_name=profile_name)
    ssm_client = client_session.client(
        "ssm",
        region_name=region_name,
        config=construct_boto_client_retry_config(max_attempts),
    )

    return ssm_client


def get_parameters_by_tags(
    ssm_manager, parameter_tags: Sequence[Dict[str, Any]], with_decryption: bool
) -> Dict[str, str]:
    """Return a dictionary of AWS Secrets Manager names to arns
    for any secret tagged with `secrets_tag`.
    """
    parameter_names = []
    paginator = ssm_manager.get_paginator("describe_parameters")
    for parameter_tag in parameter_tags:
        filter_spec = {
            "Key": f"tag:{parameter_tag['key']}",
        }
        if parameter_tag.get("values"):
            filter_spec.update(Values=parameter_tag["values"])

        for page in paginator.paginate(
            ParameterFilters=[filter_spec],
        ):
            for param in page["Parameters"]:
                parameter_names.append(param["Name"])
    if not parameter_names:
        return {}
    else:
        return get_parameters_by_name(ssm_manager, parameter_names, with_decryption)


def get_parameters_by_name(
    ssm_manager, parameter_names: List[str], with_decryption: bool
) -> Dict[str, str]:
    """Return a dictionary of AWS Parameter Store parameter names and their values."""
    parameter_values = {}
    for retrieved in ssm_manager.get_parameters(
        Names=parameter_names, WithDecryption=with_decryption
    )["Parameters"]:
        parameter_values[retrieved["Name"]] = retrieved["Value"]

    return parameter_values


def get_parameters_by_paths(
    ssm_manager, parameter_paths: List[Dict[str, str]], with_decryption: bool, recursive: bool
) -> Dict[str, str]:
    """Returns a dictionary of AWS Parameter Store parameter names and their values that match a list of paths. If
    recursive == True, then return all parameters that are prefixed by the given path.
    """
    parameter_values = {}
    for path in parameter_paths:
        paginator = ssm_manager.get_paginator("get_parameters_by_path")
        for page in paginator.paginate(
            Path=path, Recursive=recursive, WithDecryption=with_decryption
        ):
            for parameter in page["Parameters"]:
                parameter_values[parameter["Name"]] = parameter["Value"]
    return parameter_values
