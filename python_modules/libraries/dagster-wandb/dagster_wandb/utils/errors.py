class WandbArtifactsIOManagerError(Exception):
    """Represents an execution error of the W&B Artifacts IO Manager."""

    def __init__(self, message="A W&B Artifacts IO Manager error occurred."):
        self.message = message
        super().__init__(self.message)


SUPPORTED_READ_CONFIG_KEYS = [
    "alias",
    "get_path",
    "get",
    "name",
    "partitions",
    "version",
]
SUPPORTED_WRITE_CONFIG_KEYS = [
    "add_dirs",
    "add_files",
    "add_references",
    "aliases",
    "description",
    "name",
    "partitions",
    "serialization_module",
    "type",
]
SUPPORTED_PARTITION_CONFIG_KEYS = ["get", "get_path", "version", "alias"]


def raise_on_empty_configuration(partition_key, dictionary):
    if dictionary is not None and len(dictionary) == 0:
        raise WandbArtifactsIOManagerError(
            f"The configuration is empty for the partition identified by the key '{partition_key}'."
            " This happened within the 'wandb_artifact_configuration' metadata dictionary."
        )


def raise_on_unknown_keys(supported_config_keys, dictionary, is_read_config):
    if dictionary is None:
        return

    unsupported_keys = [key for key in dictionary.keys() if key not in supported_config_keys]
    if len(unsupported_keys) > 0:
        if is_read_config:
            raise WandbArtifactsIOManagerError(
                f"The configuration keys '{unsupported_keys}' you are trying to use are not"
                " supported within the 'wandb_artifact_configuration' metadata dictionary when"
                " reading an Artifact."
            )
        else:
            raise WandbArtifactsIOManagerError(
                f"The configuration keys '{unsupported_keys}' you are trying to use are not"
                " supported within the 'wandb_artifact_configuration' metadata dictionary when"
                " writing an Artifact."
            )


def raise_on_unknown_write_configuration_keys(dictionary):
    raise_on_unknown_keys(SUPPORTED_WRITE_CONFIG_KEYS, dictionary, False)


def raise_on_unknown_read_configuration_keys(dictionary):
    raise_on_unknown_keys(SUPPORTED_READ_CONFIG_KEYS, dictionary, True)


def raise_on_unknown_partition_keys(partition_key, dictionary):
    if dictionary is None:
        return

    unsupported_keys = [
        key for key in dictionary.keys() if key not in SUPPORTED_PARTITION_CONFIG_KEYS
    ]
    if len(unsupported_keys) > 0:
        raise WandbArtifactsIOManagerError(
            f"The configuration keys '{unsupported_keys}' you are trying to use are not supported"
            f" for the partition identified by the key '{partition_key}'. This happened within the"
            " 'wandb_artifact_configuration' metadata dictionary."
        )
