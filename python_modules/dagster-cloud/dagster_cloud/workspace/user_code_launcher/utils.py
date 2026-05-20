import hashlib
import json
import os
import uuid

import yaml
from dagster._core.instance.ref import InstanceRef
from dagster._serdes import serialize_value
from dagster_cloud_cli.core.workspace import CodeLocationDeployData

DEFAULT_CODE_SERVER_PORT = 4000


def get_code_server_port() -> int:
    """Returns the code server port from DAGSTER_CLOUD_CODE_SERVER_PORT env var.

    Defaults to 4000 if the environment variable is not set.
    """
    port_str = os.environ.get("DAGSTER_CLOUD_CODE_SERVER_PORT")
    if port_str is None:
        return DEFAULT_CODE_SERVER_PORT
    return int(port_str)


def unique_resource_name(deployment_name, location_name, length_limit, sanitize_fn):
    hash_value = str(uuid.uuid4().hex)[0:6]

    name = f"{location_name}-{deployment_name}"
    sanitized_location_name = sanitize_fn(name) if sanitize_fn else name
    truncated_location_name = sanitized_location_name[: (length_limit - 7)]
    sanitized_unique_name = (
        f"{truncated_location_name}-{hash_value}" if truncated_location_name else hash_value
    )
    assert len(sanitized_unique_name) <= length_limit
    return sanitized_unique_name


def get_human_readable_label(name, length_limit, sanitize_fn):
    truncated_name = name[:length_limit]
    return sanitize_fn(truncated_name) if sanitize_fn else truncated_name


def deterministic_label_for_location(deployment_name: str, location_name: str) -> str:
    """Need a label here that is a unique function of location name since we use it to
    search for existing deployments on update and remove them. Does not need to be human-readable.
    """
    m = hashlib.sha1()  # Creates a 40-byte hash
    m.update(f"{deployment_name}-{location_name}".encode())

    unique_label = m.hexdigest()
    return unique_label


def get_instance_ref_for_user_code(instance_ref: InstanceRef) -> InstanceRef:
    # Remove fields from InstanceRef that may not be compatible with earlier
    # versions of dagster and aren't actually needed by user code

    custom_instance_class_data = instance_ref.custom_instance_class_data
    if custom_instance_class_data:
        config_dict = custom_instance_class_data.config_dict
        new_config_dict = {
            key: val
            for key, val in config_dict.items()
            if key
            not in {
                "agent_queues",
                "allowed_full_deployment_locations",
                "allowed_branch_deployment_locations",
            }
        }

        user_code_launcher_config = config_dict.get("user_code_launcher", {}).get("config")
        if user_code_launcher_config:
            new_config_dict["user_code_launcher"]["config"] = {
                key: val
                for key, val in user_code_launcher_config.items()
                if key not in {"agent_metrics"}
            }

        custom_instance_class_data = custom_instance_class_data._replace(
            config_yaml=yaml.dump(new_config_dict)
        )

    return instance_ref._replace(custom_instance_class_data=custom_instance_class_data)


def get_grpc_server_env(
    code_location_deploy_data: CodeLocationDeployData,
    port: int | None,
    location_name: str,
    instance_ref: InstanceRef | None,
    socket: str | None = None,
) -> dict[str, str]:
    return {
        **{
            "DAGSTER_LOCATION_NAME": location_name,
            "DAGSTER_INJECT_ENV_VARS_FROM_INSTANCE": "1",
            "DAGSTER_CLI_API_GRPC_LAZY_LOAD_USER_CODE": "1",
            "DAGSTER_CLI_API_GRPC_HOST": "0.0.0.0",
            # include the container context on the code server to ensure that it is uploaded
            # to the server and included in the workspace snapshot, which ensures that while a
            # code location is still being updated, existing code will use the snapshotted
            # version rather than the newly updated version
            "DAGSTER_CONTAINER_CONTEXT": json.dumps(code_location_deploy_data.container_context),
        },
        **(
            {"DAGSTER_INSTANCE_REF": serialize_value(get_instance_ref_for_user_code(instance_ref))}
            if instance_ref
            else {}
        ),
        **({"DAGSTER_CLI_API_GRPC_PORT": str(port)} if port else {}),
        **({"DAGSTER_CLI_API_GRPC_SOCKET": str(socket)} if socket else {}),
        **(
            {"DAGSTER_CURRENT_IMAGE": code_location_deploy_data.image}
            if code_location_deploy_data.image
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_PYTHON_FILE": code_location_deploy_data.python_file}
            if code_location_deploy_data.python_file
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_MODULE_NAME": code_location_deploy_data.module_name}
            if code_location_deploy_data.module_name
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_PACKAGE_NAME": code_location_deploy_data.package_name}
            if code_location_deploy_data.package_name
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_WORKING_DIRECTORY": code_location_deploy_data.working_directory}
            if code_location_deploy_data.working_directory
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_ATTRIBUTE": code_location_deploy_data.attribute}
            if code_location_deploy_data.attribute
            else {}
        ),
        **(
            {"DAGSTER_CLI_API_GRPC_USE_PYTHON_ENVIRONMENT_ENTRY_POINT": "1"}
            if code_location_deploy_data.executable_path
            else {}
        ),
        **(
            {
                "DAGSTER_CLI_API_GRPC_AUTOLOAD_DEFS_MODULE_NAME": code_location_deploy_data.autoload_defs_module_name
            }
            if code_location_deploy_data.autoload_defs_module_name
            else {}
        ),
    }
