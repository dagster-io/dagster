import os
import pickle

from dagster_wandb.utils.errors import WandbArtifactsIOManagerError

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

dill = None
cloudpickle = None
joblib = None


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


def pickle_artifact_content(
    context, serialization_module_name, serialization_module_parameters_with_protocol, artifact, obj
):
    if serialization_module_name == "dill":
        if not has_dill:
            raise WandbArtifactsIOManagerError(
                "No module named 'dill' found. Please, make sure that the module is installed."
            )
        artifact.metadata = {
            **artifact.metadata,
            **{
                "source_serialization_module": "dill",
                "source_dill_version_used": dill.__version__,  # pyright: ignore[reportOptionalMemberAccess]
                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                    "protocol"
                ],
            },
        }
        with artifact.new_file(DILL_FILENAME, "wb") as file:
            try:
                dill.dump(  # pyright: ignore[reportOptionalMemberAccess]
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
                "source_cloudpickle_version_used": cloudpickle.__version__,  # pyright: ignore[reportOptionalMemberAccess]
                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                    "protocol"
                ],
            },
        }
        with artifact.new_file(CLOUDPICKLE_FILENAME, "wb") as file:
            try:
                cloudpickle.dump(  # pyright: ignore[reportOptionalMemberAccess]
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
                "No module named 'joblib' found. Please, make sure that the module is installed."
            )
        artifact.metadata = {
            **artifact.metadata,
            **{
                "source_serialization_module": "joblib",
                "source_joblib_version_used": joblib.__version__,  # pyright: ignore[reportOptionalMemberAccess]
                "source_pickle_protocol_used": serialization_module_parameters_with_protocol[
                    "protocol"
                ],
            },
        }
        with artifact.new_file(JOBLIB_FILENAME, "wb") as file:
            try:
                joblib.dump(  # pyright: ignore[reportOptionalMemberAccess]
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


def unpickle_artifact_content(artifact_dir):
    if os.path.exists(f"{artifact_dir}/{DILL_FILENAME}"):
        if not has_dill:
            raise WandbArtifactsIOManagerError(
                "An object pickled with 'dill' was found in the Artifact. But the module"
                " was not found. Please, make sure it's installed."
            )
        with open(f"{artifact_dir}/{DILL_FILENAME}", "rb") as file:
            input_value = dill.load(file)  # pyright: ignore[reportOptionalMemberAccess]
            return input_value
    elif os.path.exists(f"{artifact_dir}/{CLOUDPICKLE_FILENAME}"):
        if not has_cloudpickle:
            raise WandbArtifactsIOManagerError(
                "An object pickled with 'cloudpickle' was found in the Artifact. But the"
                " module was not found. Please, make sure it's installed."
            )
        with open(f"{artifact_dir}/{CLOUDPICKLE_FILENAME}", "rb") as file:
            input_value = cloudpickle.load(file)  # pyright: ignore[reportOptionalMemberAccess]
            return input_value
    elif os.path.exists(f"{artifact_dir}/{JOBLIB_FILENAME}"):
        if not has_joblib:
            raise WandbArtifactsIOManagerError(
                "An object pickled with 'joblib' was found in the Artifact. But the module"
                " was not found. Please, make sure it's installed."
            )
        with open(f"{artifact_dir}/{JOBLIB_FILENAME}", "rb") as file:
            input_value = joblib.load(file)  # pyright: ignore[reportOptionalMemberAccess]
            return input_value
    elif os.path.exists(f"{artifact_dir}/{PICKLE_FILENAME}"):
        with open(f"{artifact_dir}/{PICKLE_FILENAME}", "rb") as file:
            input_value = pickle.load(file)
            return input_value
