"""
This module contains the mlflow resource provided by the MlFlow
class. This resource provides an easy way to configure mlflow for logging various
things from dagster runs.
"""
import atexit
import sys
from itertools import islice
from os import environ
from typing import Optional

import mlflow
from dagster import Field, Noneable, Permissive, failure_hook, resource
from dagster.core.definitions.decorators.hook import success_hook
from mlflow.entities.run_status import RunStatus

CONFIG_SCHEMA = {
    "experiment_name": Field(str, is_required=True, description="MlFlow experiment name."),
    "mlflow_tracking_uri": Field(
        Noneable(str),
        default_value=None,
        is_required=False,
        description="MlFlow tracking server uri.",
    ),
    "parent_run_id": Field(
        Noneable(str),
        default_value=None,
        is_required=False,
        description="Mlflow run ID of parent run if this is a nested run.",
    ),
    "env": Field(Permissive(), description="Environment variables for mlflow setup."),
    "env_to_tag": Field(
        Noneable(list),
        default_value=None,
        is_required=False,
        description="List of environment variables to log as tags in mlflow.",
    ),
    "extra_tags": Field(Permissive(), description="Any extra key-value tags to log to mlflow."),
}


class MlflowMeta(type):
    """Mlflow Metaclass to create methods that "inherit" all of Mlflow's
    methods. If the class has a method defined it is excluded from the
    attribute setting from mlflow.
    """

    def __new__(cls, name, bases, attrs):
        class_cls = super(MlflowMeta, cls).__new__(cls, name, bases, attrs)
        for attr in (attr for attr in dir(mlflow) if attr not in dir(class_cls)):
            mlflow_attribute = getattr(mlflow, attr)
            if callable(mlflow_attribute):
                setattr(class_cls, attr, staticmethod(mlflow_attribute))
            else:
                setattr(class_cls, attr, mlflow_attribute)
        return class_cls


class MlFlow(metaclass=MlflowMeta):
    """Class for setting up an mlflow resource for dagster runs.
    This takes care of all the configuration required to use mlflow tracking and the complexities of
    mlflow tracking dagster parallel runs.
    """

    def __init__(self, context):

        # Context associated attributes
        self.log = context.log
        self.run_name = context.pipeline_run.pipeline_name
        self.dagster_run_id = context.run_id

        # resource config attributes
        resource_config = context.resource_config
        self.tracking_uri = resource_config.get("mlflow_tracking_uri")
        if self.tracking_uri:
            mlflow.set_tracking_uri(self.tracking_uri)
        self.parent_run_id = resource_config.get("parent_run_id")
        self.experiment_name = resource_config["experiment_name"]
        self.env_tags_to_log = resource_config.get("env_to_tag") or []
        self.extra_tags = resource_config.get("extra_tags")

        # Update env variables if any are given
        self.env_vars = resource_config.get("env", {})
        if self.env_vars:
            environ.update(self.env_vars)

        # If the experiment exists then the set won't do anything
        mlflow.set_experiment(self.experiment_name)
        self.experiment = mlflow.get_experiment_by_name(self.experiment_name)

        # Get the client object
        self.tracking_client = mlflow.tracking.MlflowClient()

        # Set up the active run and tags
        self._setup()

    def _setup(self):
        """
        Sets the active run and tags. If an Mlflow run_id exists then the
        active run is set to it. This way a single Dagster run outputs data
        to the same Mlflow run, even when multiprocess executors are used.
        """
        # Get the run id
        run_id = self._get_current_run_id()
        self._set_active_run(run_id=run_id)
        self._set_all_tags()

        # hack needed to stop mlflow from marking run as finished when
        # a process exits in parallel runs
        atexit.unregister(mlflow.end_run)

    def _get_current_run_id(
        self, experiment: Optional[str] = None, dagster_run_id: Optional[str] = None
    ):
        """Gets the run id of a specific dagster run and experiment id.
        If it doesn't exist then it returns a None.

        Args:
            experiment (optional): Mlflow experiment.
            When none is passed it fetches the experiment object set in
            the constructor.  Defaults to None.
            dagster_run_id (optional): The Dagster run id.
            When none is passed it fetches the dagster_run_id object set in
            the constructor.  Defaults to None.
        Returns:
            run_id (str or None): run_id if it is found else None
        """
        experiment = experiment or self.experiment
        dagster_run_id = dagster_run_id or self.dagster_run_id
        if experiment:
            # Check if a run with this dagster run id has already been started
            # in mlflow, will get an empty dataframe if not
            current_run_df = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.dagster_run_id='{dagster_run_id}'",
            )
            if not current_run_df.empty:
                return current_run_df.run_id.values[0]

    def _set_active_run(self, run_id=None):
        """
        This method sets the active run to be that of the specified
        run_id. If None is passed then a new run is started. The new run also
        takes care of nested runs.

        Args:
            run_id (str, optional): Mlflow run_id. Defaults to None.
        """
        nested_run = False
        if self.parent_run_id is not None:
            self._start_run(run_id=self.parent_run_id, run_name=self.run_name)
            nested_run = True
        self._start_run(run_id=run_id, run_name=self.run_name, nested=nested_run)

    def _start_run(self, **kwargs):
        """
        Catches the Mlflow exception if a run is already active.
        """

        try:
            run = mlflow.start_run(**kwargs)
            self.log.info(
                f"Starting a new mlflow run with id {run.info.run_id} "
                f"in experiment {self.experiment_name}"
            )
        except Exception as ex:
            run = mlflow.active_run()
            if f"is already active" not in str(ex):
                raise (ex)
            self.log.info(f"Run with id {run.info.run_id} is already active.")

    def _set_all_tags(self):
        """Method collects dagster_run_id plus all env variables/tags that have been
            specified by the user in the config_schema and logs them as tags in mlflow.

        Returns:
            tags [dict]: Dictionary of all the tags
        """
        tags = {tag: environ.get(tag) for tag in self.env_tags_to_log}
        tags["dagster_run_id"] = self.dagster_run_id
        if self.extra_tags:
            tags.update(self.extra_tags)

        mlflow.set_tags(tags)

    def cleanup_on_error(self):
        """Method ends mlflow run with correct exit status for failed runs. Note that
        this method does not work when a pipeline running in dagit fails, it seems
        that in this case a different process runs the pipeline and when it fails
        the stack trace is therefore not available. For this case we can use the
        cleanup_on_failure hook defined below.
        """
        any_error = sys.exc_info()

        if any_error[1]:
            if isinstance(any_error[1], KeyboardInterrupt):
                mlflow.end_run(status=RunStatus.to_string(RunStatus.KILLED))
            else:
                mlflow.end_run(status=RunStatus.to_string(RunStatus.FAILED))

    @staticmethod
    def log_params(params: dict):
        """Overload of the mlflow.log_params. If len(params) >100 then
        params is sent to mlflow in chunks.

        Args:
            params (dict): Parameters to be logged
        """
        for param_chunk in MlFlow.chunks(params, 100):
            mlflow.log_params(param_chunk)

    @staticmethod
    def chunks(params: dict, size: int = 100):
        """Method that chunks a dictionary into batches of size.

        Args:
            params (dict): Dictionary set to be batched
            size (int, optional): Number of batches. Defaults to 100.

        Yields:
            (dict): Batch of dictionary
        """
        it = iter(params)
        for _ in range(0, len(params), size):
            yield {k: params[k] for k in islice(it, size)}


@failure_hook(required_resource_keys={"mlflow"})
def cleanup_on_dagit_failure(context):
    """When attached to a pipeline this hook will be called when a pipeline running
    in dagit fails. Note that this hook is only called when the failing pipeline
    has been launched through dagit. We therefore still need the cleanup_on_error
    method above to cover all other cases.
    """

    mlf = context.resources.mlflow
    mlf.end_run(status=RunStatus.to_string(RunStatus.FAILED))


@success_hook(required_resource_keys={"mlflow"})
def cleanup_on_success(context):
    """
    When attached to a pipeline this hook will be called whenever a solid runs
    successfully.
    """
    _cleanup_on_success(context)


def _cleanup_on_success(context):
    """
    Checks if the current solid in the context is the last solid in the pipeline
    and ends the mlflow run with a successful status when this is the case.
    """
    last_solid_name = context.pipeline_def.solids_in_topological_order[-1].name

    if context.solid.name == last_solid_name:
        context.resources.mlflow.end_run()


@resource(config_schema=CONFIG_SCHEMA)
def mlflow_tracking(context):
    """
    This resource provides access to all of mlflow's methods as well as the mlflow tracking client's
    methods.

    Usage:

    1. Make sure to add the mlflow resource to the first solid in the pipeline to start
       the mlflow run.
    2. To use mlflow utilities inside a solid make sure to add the mlflow resource to
       that solid and then get the mlflow instance like so
       `mlf = context.resources.mlflow`
       then use as you would normally use mlflow,
       e.g.; `mlf.log_params(some_params)`
    3. Add the success and failure hooks namely `cleanup_on_success` and `cleanup_on_dagit_failure`
       to your pipeline to ensure the mlflow run is always stopped with the correct run status.


    Examples:

        .. code-block:: python

            from dagster_mlflow import mlflow_tracking, cleanup_on_success, cleanup_on_dagit_failure

            @solid(required_resource_keys={"mlflow"})
            def mlflow_solid(context):
                mlf = context.resources.mlflow

                mlf.log_params(some_params)
                mlf.tracking_client.create_registered_model(some_model_name)

            @cleanup_on_success
            @cleanup_on_dagit_failure
            @pipeline(mode_defs=[ModeDefinition(resource_defs={"mlflow": mlflow_tracking})])
            def mlf_pipeline():
                mlflow_solid()

            # example pipeline using an mlflow instance with s3 storage
            result = execute_pipeline(
                mlf_pipeline,
                run_config = {
                    "resources": {
                        "mlflow": {
                            "config": {
                                "experiment_name": my_experiment,
                                "mlflow_tracking_uri": http://localhost:5000,

                                # if want to run a nested run, provide parent_run_id
                                "parent_run_id": an_existing_mlflow_run_id,

                                # env variables to pass to mlflow
                                "env": {
                                    "MLFLOW_S3_ENDPOINT_URL": my_s3_endpoint,
                                    "AWS_ACCESS_KEY_ID": my_aws_key_id,
                                    "AWS_SECRET_ACCESS_KEY": my_secret,
                                },

                                # env variables you want to log as mlflow tags
                                "env_to_tag":
                                    - DOCKER_IMAGE_TAG

                                # key-value tags to add to your experiment
                                "extra_tags":
                                    super: experiment
                            }
                        }
                    }
                }
            )

    """
    mlf = MlFlow(context)
    yield mlf
    mlf.cleanup_on_error()
