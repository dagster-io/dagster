from dagster import Bool, Field, Noneable, Permissive, String
from dagster._core.types.dagster_type import Array


def launch_config():
    return {
        "uri": Field(
            config=String, is_required=False, description="A W&B run URI or a Git repository URI."
        ),
        "job": Field(
            config=String,
            is_required=False,
            description=(
                "Name of the job to Launch (removes the need for 'uri') e.g."
                " 'wandb/test/my-job:latest'."
            ),
        ),
        "queue": Field(
            config=String,
            is_required=False,
            description="The name of the queue to enqueue the run to.",
        ),
        "entry_point": Field(
            config=Array(str),
            is_required=False,
            description=(
                "Entry point within project. Default to 'main.py'. If the entry point is not found,"
                " attempts to run the project file with the specified name as a script, using"
                " 'python' to run .py files and the default shell (specified by environment"
                " variable $SHELL) to run .sh files. If passed in, will override the entrypoint"
                " value passed in using a config."
            ),
        ),
        "version": Field(
            config=String,
            is_required=False,
            description="For Git-based projects, either a commit hash or a branch name.",
        ),
        "parameters": Field(
            config=Noneable(Permissive()),
            is_required=False,
            description=(
                "A dictionary containing parameters for the entry point command. Defaults to using"
                " the the parameters used to run the original run."
            ),
        ),
        "name": Field(
            config=String,
            is_required=False,
            description=(
                "Name of the run under which to launch the run. If not specified, a random run name"
                " will be used."
            ),
        ),
        "resource": Field(
            config=String,
            is_required=False,
            description=(
                "Execution resource to use for run. If passed in, will override the resource value"
                " passed in using a config file. Defaults to 'local'"
            ),
        ),
        "resource_args": Field(
            config=Noneable(Permissive()),
            is_required=False,
            description=(
                "Parameters to the Launch execution resource. This isn't used when launching"
                " locally."
            ),
        ),
        "docker_image": Field(
            config=String,
            is_required=False,
            description=(
                "Specific Docker image to use. In the form 'name:tag'. If passed in, will override"
                " the docker image value passed in a config."
            ),
        ),
        "config": Field(
            config=Noneable(Permissive()),
            is_required=False,
            description=(
                "A dictionary containing the configuration for the run. May also contain resource"
                " specific arguments under the key 'resource_args'. See Launch integration"
                " documentation for reference."
            ),
        ),
        "synchronous": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description="Whether to block while waiting for a run to complete. Defaults to True.",
        ),
        "cuda": Field(
            config=Bool,
            is_required=False,
            description=(
                "When set to True or when reproducing a previous GPU run, builds a CUDA-enabled"
                " image."
            ),
        ),
        "run_id": Field(
            config=String,
            is_required=False,
            description="ID for the run to reproduce.",
        ),
    }


def launch_agent_config():
    return {
        "queues": Field(
            Array(String), is_required=False, description="List of queue names to poll."
        ),
        "max_jobs": Field(
            int,
            is_required=False,
            description=(
                "The maximum number of launch jobs this agent can run in parallel. Defaults to 1."
                " Set to -1 for no upper limit."
            ),
        ),
    }
