import datetime
import os
import pickle
import platform
import shutil
import sys
import time
from contextlib import contextmanager
from typing import List, Optional

from dagster import (
    Field,
    InitResourceContext,
    InputContext,
    Int,
    IOManager,
    MetadataValue,
    OutputContext,
    String,
    io_manager,
)
from wandb.sdk.data_types.base_types.wb_value import WBValue
from wandb.sdk.wandb_artifacts import Artifact

from .resources import WANDB_CLOUD_HOST
from .version import __version__

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

try:
    import dill

    has_dill = True
except ImportError:
    has_dill = False

try:
    import cloudpickle

    has_cloudpickle = True
except ImportError:
    has_cloudpickle = False

try:
    import joblib

    has_joblib = True
except ImportError:
    has_joblib = False


PICKLE_FILENAME = "output.pickle"
DILL_FILENAME = "output.dill"
CLOUDPICKLE_FILENAME = "output.cloudpickle"
JOBLIB_FILENAME = "output.joblib"
ACCEPTED_SERIALIZATION_MODULES = [
    "dill",
    "cloudpickle",
    "joblib",
    "pickle",
]


class Config(TypedDict):
    dagster_run_id: str
    wandb_host: str
    wandb_entity: str
    wandb_project: str
    wandb_run_name: Optional[str]
    wandb_run_id: Optional[str]
    wandb_run_tags: Optional[List[str]]
    base_dir: str
    cache_duration_in_minutes: Optional[int]


class WandbArtifactsIOManagerError(Exception):
    """Represents an execution error of the W&B Artifacts IO Manager."""

    def __init__(self, message="A W&B Artifacts IO Manager error occurred."):
        self.message = message
        super().__init__(self.message)


class ArtifactsIOManager(IOManager):
    """IO Manager to handle Artifacts in Weights & Biases (W&B) .

    It handles 3 different inputs:
    - Pickable objects (the serialization module is configurable)
    - W&B Objects (Audio, Table, Image, etc)
    - W&B Artifacts
    """

    def __init__(self, wandb_client, config: Config):
        self.wandb = wandb_client

        dagster_run_id = config["dagster_run_id"]
        self.dagster_run_id = dagster_run_id
        self.wandb_host = config["wandb_host"]
        self.wandb_entity = config["wandb_entity"]
        self.wandb_project = config["wandb_project"]
        self.wandb_run_id = config.get("wandb_run_id") or dagster_run_id
        self.wandb_run_name = config.get("wandb_run_name") or f"dagster-run-{dagster_run_id[0:8]}"
        # augments the run tags
        wandb_run_tags = config["wandb_run_tags"] or []
        if "dagster_wandb" not in wandb_run_tags:
            wandb_run_tags = [*wandb_run_tags, "dagster_wandb"]
        self.wandb_run_tags = wandb_run_tags

        self.base_dir = config["base_dir"]
        cache_duration_in_minutes = config["cache_duration_in_minutes"]
        default_cache_expiration_in_minutes = 60 * 24 * 30  # 60 minutes * 24 hours * 30 days
        self.cache_duration_in_minutes = (
            cache_duration_in_minutes
            if cache_duration_in_minutes is not None
            else default_cache_expiration_in_minutes
        )

    def _get_local_storage_path(self):
        path = self.base_dir
        if os.path.basename(path) != "storage":
            path = os.path.join(path, "storage")
        path = os.path.join(path, "wandb_artifacts_manager")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_artifacts_path(self, name, version):
        local_storage_path = self._get_local_storage_path()
        path = os.path.join(local_storage_path, "artifacts", f"{name}:{version}")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_wandb_logs_path(self):
        local_storage_path = self._get_local_storage_path()
        path = os.path.join(local_storage_path, "runs", self.dagster_run_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _clean_local_storage_path(self):
        local_storage_path = self._get_local_storage_path()
        cache_duration_in_minutes = self.cache_duration_in_minutes
        current_timestamp = int(time.time())
        expiration_timestamp = current_timestamp - (
            cache_duration_in_minutes * 60  # convert to seconds
        )

        for root, dirs, files in os.walk(local_storage_path, topdown=False):
            for name in files:
                current_file_path = os.path.join(root, name)
                most_recent_access = os.lstat(current_file_path).st_atime
                if most_recent_access <= expiration_timestamp or cache_duration_in_minutes == 0:
                    os.remove(current_file_path)
            for name in dirs:
                current_dir_path = os.path.join(root, name)
                if not os.path.islink(current_dir_path):
                    if len(os.listdir(current_dir_path)) == 0 or cache_duration_in_minutes == 0:
                        shutil.rmtree(current_dir_path)

    @contextmanager
    def wandb_run(self):
        self.wandb.init(
            id=self.wandb_run_id,
            name=self.wandb_run_name,
            project=self.wandb_project,
            entity=self.wandb_entity,
            dir=self._get_wandb_logs_path(),
            tags=self.wandb_run_tags,
            anonymous="never",
            resume="allow",
        )
        try:
            yield self.wandb.run
        finally:
            self.wandb.finish()
            self._clean_local_storage_path()

    def _upload_artifact(self, context: OutputContext, obj):
        with self.wandb_run() as run:
            parameters = context.metadata.get("wandb_artifact_configuration", {})  # type: ignore

            serialization_module = parameters.get("serialization_module", {})
            serialization_module_name = serialization_module.get("name", "pickle")

            if serialization_module_name not in ACCEPTED_SERIALIZATION_MODULES:
                raise WandbArtifactsIOManagerError(
                    f"The provided value '{serialization_module_name}' is not a supported"
                    f" serialization module. Supported: {ACCEPTED_SERIALIZATION_MODULES}."
                )
            serialization_module_parameters = serialization_module.get("parameters", {})
            serialization_module_parameters_with_protocol = {
                "protocol": pickle.HIGHEST_PROTOCOL,  # we use the highest available protocol if we don't pass one
                **serialization_module_parameters,
            }

            artifact_type = parameters.get("type", "artifact")
            artifact_description = parameters.get("description")
            artifact_metadata = {
                "source_integration": "dagster_wandb",
                "source_integration_version": __version__,
                "source_dagster_run_id": self.dagster_run_id,
                "source_created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source_python_version": platform.python_version(),
            }
            if isinstance(obj, Artifact):
                if parameters.get("name") is not None:
                    raise WandbArtifactsIOManagerError(
                        "A 'name' property was provided in the 'wandb_artifact_configuration'"
                        " metadata dictionary. A 'name' property can only be provided for output"
                        " that is not already an Artifact object."
                    )

                if parameters.get("type") is not None:
                    raise WandbArtifactsIOManagerError(
                        "A 'type' property was provided in the 'wandb_artifact_configuration'"
                        " metadata dictionary. A 'type' property can only be provided for output"
                        " that is not already an Artifact object."
                    )

                if context.has_partition_key:
                    raise WandbArtifactsIOManagerError(
                        "A partitioned job was detected for an output of type Artifact. This is not"
                        " currently supported. We would love to hear about your use case. Please"
                        " contact W&B Support."
                    )

                if len(serialization_module) != 0:  # not an empty dict
                    context.log.warning(
                        "A 'serialization_module' dictionary was provided in the"
                        " 'wandb_artifact_configuration' metadata dictionary. It has no effect on"
                        " an output that is already an Artifact object."
                    )

                # The obj is already an Artifact we augment its metadata
                artifact = obj

                artifact.metadata = {**artifact.metadata, **artifact_metadata}

                if artifact.description is not None and artifact_description is not None:
                    raise WandbArtifactsIOManagerError(
                        "A 'description' value was provided in the 'wandb_artifact_configuration'"
                        " metadata dictionary for an existing Artifact with a non-null description."
                        " Please, either set the description through 'wandb_artifact_argument' or"
                        " when constructing your Artifact."
                    )
                if artifact_description is not None:
                    artifact.description = artifact_description
            else:
                if context.has_asset_key:
                    if parameters.get("name") is not None:
                        raise WandbArtifactsIOManagerError(
                            "A 'name' property was provided in the 'wandb_artifact_configuration'"
                            " metadata dictionary. A 'name' property is only required when no"
                            " 'AssetKey' is found. Artifacts created from an @asset use the asset"
                            " name as the Artifact name. Artifacts created from an @op with a"
                            " specified 'asset_key' for the output will use that value. Please"
                            " remove the 'name' property."
                        )
                    artifact_name = context.get_asset_identifier()[0]  # name of asset
                else:
                    if parameters.get("name") is None:
                        raise WandbArtifactsIOManagerError(
                            "Missing 'name' property in the 'wandb_artifact_configuration' metadata"
                            " dictionary. A 'name' property is required for Artifacts created from"
                            " an @op. Alternatively you can use an @asset."
                        )
                    artifact_name = parameters.get("name")

                if context.has_partition_key:
                    artifact_name = f"{artifact_name}.{context.partition_key}"

                # Creates an artifact to hold the obj
                artifact = self.wandb.Artifact(
                    name=artifact_name,
                    type=artifact_type,
                    description=artifact_description,
                    metadata=artifact_metadata,
                )
                if isinstance(obj, WBValue):
                    if len(serialization_module) != 0:  # not an empty dict
                        context.log.warning(
                            "A 'serialization_module' dictionary was provided in the"
                            " 'wandb_artifact_configuration' metadata dictionary. It has no effect"
                            " on when the output is a W&B object."
                        )
                    # Adds the WBValue object using the class name as the name for the file
                    artifact.add(obj, obj.__class__.__name__)
                elif obj is not None:
                    # The output is not a native wandb Object, we serialize it
                    if serialization_module_name == "dill":
                        if not has_dill:
                            raise WandbArtifactsIOManagerError(
                                "No module named 'dill' found. Please, make sure that the module is"
                                " installed."
                            )
                        artifact.metadata = {
                            **artifact.metadata,
                            **{
                                "source_serialization_module": "dill",
                                "source_dill_version_used": dill.__version__,
                                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                                    "protocol"
                                ],
                            },
                        }
                        with artifact.new_file(DILL_FILENAME, "wb") as file:
                            try:
                                dill.dump(
                                    obj,
                                    file,
                                    **serialization_module_parameters_with_protocol,
                                )
                                context.log.info(
                                    "Output serialized using dill with"
                                    f" parameters={serialization_module_parameters_with_protocol}"
                                )
                            except Exception as exception:
                                raise WandbArtifactsIOManagerError(
                                    "An error occurred in the dill serialization process. Please,"
                                    " verify that the passed arguments are correct and your data is"
                                    " compatible with the module."
                                ) from exception
                    elif serialization_module_name == "cloudpickle":
                        if not has_cloudpickle:
                            raise WandbArtifactsIOManagerError(
                                "No module named 'cloudpickle' found. Please, make sure that the"
                                " module is installed."
                            )
                        artifact.metadata = {
                            **artifact.metadata,
                            **{
                                "source_serialization_module": "cloudpickle",
                                "source_cloudpickle_version_used": cloudpickle.__version__,
                                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                                    "protocol"
                                ],
                            },
                        }
                        with artifact.new_file(CLOUDPICKLE_FILENAME, "wb") as file:
                            try:
                                cloudpickle.dump(
                                    obj,
                                    file,
                                    **serialization_module_parameters_with_protocol,
                                )
                                context.log.info(
                                    "Output serialized using cloudpickle with"
                                    f" parameters={serialization_module_parameters_with_protocol}"
                                )
                            except Exception as exception:
                                raise WandbArtifactsIOManagerError(
                                    "An error occurred in the cloudpickle serialization process."
                                    " Please, verify that the passed arguments are correct and your"
                                    " data is compatible with the module."
                                ) from exception
                    elif serialization_module_name == "joblib":
                        if not has_joblib:
                            raise WandbArtifactsIOManagerError(
                                "No module named 'joblib' found. Please, make sure that the module"
                                " is installed."
                            )
                        artifact.metadata = {
                            **artifact.metadata,
                            **{
                                "source_serialization_module": "joblib",
                                "source_joblib_version_used": joblib.__version__,
                                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                                    "protocol"
                                ],
                            },
                        }
                        with artifact.new_file(JOBLIB_FILENAME, "wb") as file:
                            try:
                                joblib.dump(
                                    obj,
                                    file,
                                    **serialization_module_parameters_with_protocol,
                                )
                                context.log.info(
                                    "Output serialized using joblib with"
                                    f" parameters={serialization_module_parameters_with_protocol}"
                                )
                            except Exception as exception:
                                raise WandbArtifactsIOManagerError(
                                    "An error occurred in the joblib serialization process. Please,"
                                    " verify that the passed arguments are correct and your data is"
                                    " compatible with the module."
                                ) from exception
                    else:
                        artifact.metadata = {
                            **artifact.metadata,
                            **{
                                "source_serialization_module": "pickle",
                                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                                    "protocol"
                                ],
                            },
                        }
                        with artifact.new_file(PICKLE_FILENAME, "wb") as file:
                            try:
                                pickle.dump(
                                    obj,
                                    file,
                                    **serialization_module_parameters_with_protocol,
                                )
                                context.log.info(
                                    "Output serialized using pickle with"
                                    f" parameters={serialization_module_parameters_with_protocol}"
                                )
                            except Exception as exception:
                                raise WandbArtifactsIOManagerError(
                                    "An error occurred in the pickle serialization process."
                                    " Please, verify that the passed arguments are correct and"
                                    " your data is compatible with pickle. Otherwise consider"
                                    " using another module. Supported serialization:"
                                    f" {ACCEPTED_SERIALIZATION_MODULES}."
                                ) from exception

            # Add any files: https://docs.wandb.ai/ref/python/artifact#add_file
            add_files = parameters.get("add_files")
            if add_files is not None and len(add_files) > 0:
                for add_file in add_files:
                    artifact.add_file(**add_file)

            # Add any dirs: https://docs.wandb.ai/ref/python/artifact#add_dir
            add_dirs = parameters.get("add_dirs")
            if add_dirs is not None and len(add_dirs) > 0:
                for add_dir in add_dirs:
                    artifact.add_dir(**add_dir)

            # Add any reference: https://docs.wandb.ai/ref/python/artifact#add_reference
            add_references = parameters.get("add_references")
            if add_references is not None and len(add_references) > 0:
                for add_reference in add_references:
                    artifact.add_reference(**add_reference)

            # Augments the aliases
            aliases = parameters.get("aliases", [])
            aliases.append(f"dagster-run-{self.dagster_run_id[0:8]}")
            if "latest" not in aliases:
                aliases.append("latest")

            # Logs the artifact
            self.wandb.log_artifact(artifact, aliases=aliases)
            artifact.wait()

            # Adds useful metadata to the output or Asset

            artifacts_base_url = (
                "https://wandb.ai"
                if self.wandb_host == WANDB_CLOUD_HOST
                else self.wandb_host.rstrip("/")
            )
            output_metadata = {
                "dagster_run_id": MetadataValue.dagster_run(self.dagster_run_id),
                "wandb_artifact_id": MetadataValue.text(artifact.id),  # type: ignore
                "wandb_artifact_type": MetadataValue.text(artifact.type),
                "wandb_artifact_version": MetadataValue.text(artifact.version),
                "wandb_artifact_size": MetadataValue.int(artifact.size),
                "wandb_artifact_url": MetadataValue.url(
                    f"{artifacts_base_url}/{run.entity}/{run.project}/artifacts/{artifact.type}/{artifact.id}/{artifact.version}"
                ),
                "wandb_entity": MetadataValue.text(run.entity),
                "wandb_project": MetadataValue.text(run.project),
                "wandb_run_id": MetadataValue.text(run.id),
                "wandb_run_name": MetadataValue.text(run.name),
                "wandb_run_path": MetadataValue.text(run.path),
                "wandb_run_url": MetadataValue.url(run.url),
            }
            context.add_output_metadata(output_metadata)

    def _download_artifact(self, context: InputContext):
        with self.wandb_run() as run:
            parameters = context.metadata.get("wandb_artifact_configuration", {})  # type: ignore

            artifact_alias = parameters.get("alias")
            artifact_version = parameters.get("version")

            if artifact_alias is not None and artifact_version is not None:
                raise WandbArtifactsIOManagerError(
                    "A value for 'version' and 'alias' have been provided. Only one property can be"
                    " used at the same time."
                )

            artifact_identifier = artifact_alias or artifact_version or "latest"

            if context.has_asset_key:
                artifact_name = context.get_asset_identifier()[0]  # name of asset
            else:
                artifact_name = parameters.get("name")
                if artifact_name is None:
                    raise WandbArtifactsIOManagerError(
                        "Missing 'name' property in the 'wandb_artifact_configuration' metadata"
                        " dictionary. A 'name' property is required for Artifacts used in an @op."
                        " Alternatively you can use an @asset."
                    )

            if context.has_partition_key:
                artifact_name = f"{artifact_name}.{context.partition_key}"

            artifact = run.use_artifact(
                f"{run.entity}/{run.project}/{artifact_name}:{artifact_identifier}"
            )

            name = parameters.get("get")
            path = parameters.get("get_path")
            if name is not None and path is not None:
                raise WandbArtifactsIOManagerError(
                    "A value for 'get' and 'get_path' has been provided in the"
                    " 'wandb_artifact_configuration' metadata dictionary. Only one property can be"
                    " used. Alternatively you can use neither and the entire Artifact will be"
                    " dowloaded."
                )

            if name is not None:
                return artifact.get(name)

            artifacts_path = self._get_artifacts_path(artifact_name, artifact.version)
            if path is not None:
                path = artifact.get_path(path)
                return path.download(root=artifacts_path)

            artifact_dir = artifact.download(root=artifacts_path, recursive=True)

            if os.path.exists(f"{artifact_dir}/{DILL_FILENAME}"):
                if not has_dill:
                    raise WandbArtifactsIOManagerError(
                        "An object pickled with 'dill' was found in the Artifact. But the module"
                        " was not found. Please, make sure it's installed."
                    )
                with open(f"{artifact_dir}/{DILL_FILENAME}", "rb") as file:
                    input_value = dill.load(file)
                    return input_value
            elif os.path.exists(f"{artifact_dir}/{CLOUDPICKLE_FILENAME}"):
                if not has_cloudpickle:
                    raise WandbArtifactsIOManagerError(
                        "An object pickled with 'cloudpickle' was found in the Artifact. But the"
                        " module was not found. Please, make sure it's installed."
                    )
                with open(f"{artifact_dir}/{CLOUDPICKLE_FILENAME}", "rb") as file:
                    input_value = cloudpickle.load(file)
                    return input_value
            elif os.path.exists(f"{artifact_dir}/{JOBLIB_FILENAME}"):
                if not has_joblib:
                    raise WandbArtifactsIOManagerError(
                        "An object pickled with 'joblib' was found in the Artifact. But the module"
                        " was not found. Please, make sure it's installed."
                    )
                with open(f"{artifact_dir}/{JOBLIB_FILENAME}", "rb") as file:
                    input_value = joblib.load(file)
                    return input_value
            elif os.path.exists(f"{artifact_dir}/{PICKLE_FILENAME}"):
                with open(f"{artifact_dir}/{PICKLE_FILENAME}", "rb") as file:
                    input_value = pickle.load(file)
                    return input_value

            artifact.verify(root=artifacts_path)
            return artifact

    def handle_output(self, context: OutputContext, obj) -> None:
        if obj is None:
            context.log.warning(
                "The output value passed to W&B IO Manager is empty. Ignore if expected."
            )
        else:
            try:
                self._upload_artifact(context, obj)
            except WandbArtifactsIOManagerError as exception:
                raise exception
            except Exception as exception:
                raise WandbArtifactsIOManagerError() from exception

    def load_input(self, context: InputContext):
        try:
            return self._download_artifact(context)
        except WandbArtifactsIOManagerError as exception:
            raise exception
        except Exception as exception:
            raise WandbArtifactsIOManagerError() from exception


@io_manager(
    required_resource_keys={"wandb_resource", "wandb_config"},
    description="IO manager to read and write W&B Artifacts",
    config_schema={
        "run_name": Field(
            String,
            is_required=False,
            description=(
                "Short display name for this run, which is how you'll identify this run in the UI."
                " By default, it`s set to a string with the following format dagster-run-[8 first"
                " characters of the Dagster Run ID] e.g. dagster-run-7e4df022."
            ),
        ),
        "run_id": Field(
            String,
            is_required=False,
            description=(
                "Unique ID for this run, used for resuming. It must be unique in the project, and"
                " if you delete a run you can't reuse the ID. Use the name field for a short"
                " descriptive name, or config for saving hyperparameters to compare across runs."
                r" The ID cannot contain the following special characters: /\#?%:.. You need to set"
                " the Run ID when you are doing experiment tracking inside Dagster to allow the IO"
                " Manager to resume the run. By default it`s set to the Dagster Run ID e.g "
                " 7e4df022-1bf2-44b5-a383-bb852df4077e."
            ),
        ),
        "run_tags": Field(
            [String],
            is_required=False,
            description=(
                "A list of strings, which will populate the list of tags on this run in the UI."
                " Tags are useful for organizing runs together, or applying temporary labels like"
                " 'baseline' or 'production'. It's easy to add and remove tags in the UI, or filter"
                " down to just runs with a specific tag. Any W&B Run used by the integration will"
                " have the dagster_wandb tag."
            ),
        ),
        "base_dir": Field(
            String,
            is_required=False,
            description=(
                "Base directory used for local storage and caching. W&B Artifacts and W&B Run logs"
                " will be written and read from that directory. By default, it`s using the"
                " DAGSTER_HOME directory."
            ),
        ),
        "cache_duration_in_minutes": Field(
            Int,
            is_required=False,
            description=(
                "Defines the amount of time W&B Artifacts and W&B Run logs should be kept in the"
                " local storage. Only files and directories that were not opened for that amount of"
                " time are removed from the cache. Cache purging happens at the end of an IO"
                " Manager execution. You can set it to 0, if you want to disable caching"
                " completely. Caching improves speed when an Artifact is reused between jobs"
                " running on the same machine. It defaults to 30 days."
            ),
        ),
    },
)
def wandb_artifacts_io_manager(context: InitResourceContext):
    """Dagster IO Manager to create and consume W&B Artifacts.

    It allows any Dagster @op or @asset to create and consume W&B Artifacts natively.

    For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_.

    **Example:**

    .. code-block:: python

            @repository
            def my_repository():
                return [
                    *with_resources(
                        load_assets_from_current_module(),
                        resource_defs={
                            "wandb_config": make_values_resource(
                                entity=str,
                                project=str,
                            ),
                            "wandb_resource": wandb_resource.configured(
                                {"api_key": {"env": "WANDB_API_KEY"}}
                            ),
                            "wandb_artifacts_manager": wandb_artifacts_io_manager.configured(
                                {"cache_duration_in_minutes": 60} # only cache files for one hour
                            ),
                        },
                        resource_config_by_key={
                            "wandb_config": {
                                "config": {
                                    "entity": "my_entity",
                                    "project": "my_project"
                                }
                            }
                        },
                    ),
                ]


            @asset(
                name="my_artifact",
                metadata={
                    "wandb_artifact_configuration": {
                        "type": "dataset",
                    }
                },
                io_manager_key="wandb_artifacts_manager",
            )
            def create_dataset():
                return [1, 2, 3]

    """
    wandb_client = context.resources.wandb_resource["sdk"]
    wandb_host = context.resources.wandb_resource["host"]
    wandb_entity = context.resources.wandb_config["entity"]
    wandb_project = context.resources.wandb_config["project"]

    wandb_run_name = None
    wandb_run_id = None
    wandb_run_tags = None
    cache_duration_in_minutes = None
    if context.resource_config is not None:
        wandb_run_name = context.resource_config.get("run_name")
        wandb_run_id = context.resource_config.get("run_id")
        wandb_run_tags = context.resource_config.get("run_tags")
        base_dir = context.resource_config.get(
            "base_dir",
            context.instance.storage_directory()
            if context.instance
            else os.environ["DAGSTER_HOME"],
        )
        cache_duration_in_minutes = context.resource_config.get("cache_duration_in_minutes")

    if "PYTEST_CURRENT_TEST" in os.environ:
        dagster_run_id = "unit-testing"
    else:
        dagster_run_id = context.run_id

    config: Config = {
        "dagster_run_id": dagster_run_id or "",
        "wandb_host": wandb_host,
        "wandb_entity": wandb_entity,
        "wandb_project": wandb_project,
        "wandb_run_name": wandb_run_name,
        "wandb_run_id": wandb_run_id,
        "wandb_run_tags": wandb_run_tags,
        "base_dir": base_dir,  # type: ignore
        "cache_duration_in_minutes": cache_duration_in_minutes,
    }
    return ArtifactsIOManager(wandb_client, config)
