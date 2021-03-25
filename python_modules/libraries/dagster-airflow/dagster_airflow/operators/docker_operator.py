import ast
import json
import warnings
from contextlib import contextmanager

from airflow.exceptions import AirflowException, AirflowSkipException
from dagster import check, seven
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.plan import should_skip_step
from dagster.core.instance import AIRFLOW_EXECUTION_DATE_STR, DagsterInstance
from dagster.grpc.types import ExecuteStepArgs
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster_airflow.vendor.docker_operator import DockerOperator
from docker import APIClient, from_env

from .util import check_events_for_failures, check_events_for_skips, get_aws_environment

DOCKER_TEMPDIR = "/tmp"


class DagsterDockerOperator(DockerOperator):
    """Dagster operator for Apache Airflow.

    Wraps a modified DockerOperator incorporating https://github.com/apache/airflow/pull/4315.

    Additionally, if a Docker client can be initialized using docker.from_env,
    Unlike the standard DockerOperator, this operator also supports config using docker.from_env,
    so it isn't necessary to explicitly set docker_url, tls_config, or api_version.


    Incorporates https://github.com/apache/airflow/pull/4315/ and an implementation of
    https://issues.apache.org/jira/browse/AIRFLOW-3825.

    Parameters:
    host_tmp_dir (str): Specify the location of the temporary directory on the host which will
        be mapped to tmp_dir. If not provided defaults to using the standard system temp directory.
    """

    def __init__(self, dagster_operator_parameters, *args):
        kwargs = dagster_operator_parameters.op_kwargs
        tmp_dir = kwargs.pop("tmp_dir", DOCKER_TEMPDIR)
        host_tmp_dir = kwargs.pop("host_tmp_dir", seven.get_system_temp_directory())
        self.host_tmp_dir = host_tmp_dir

        run_config = dagster_operator_parameters.run_config
        if "filesystem" in run_config["intermediate_storage"]:
            if (
                "config" in (run_config["intermediate_storage"].get("filesystem", {}) or {})
                and "base_dir"
                in (
                    (run_config["intermediate_storage"].get("filesystem", {}) or {}).get(
                        "config", {}
                    )
                    or {}
                )
                and run_config["intermediate_storage"]["filesystem"]["config"]["base_dir"]
                != tmp_dir
            ):
                warnings.warn(
                    "Found base_dir '{base_dir}' set in filesystem storage config, which was not "
                    "the tmp_dir we expected ('{tmp_dir}', mounting host_tmp_dir "
                    "'{host_tmp_dir}' from the host). We assume you know what you are doing, but "
                    "if you are having trouble executing containerized workloads, this may be the "
                    "issue".format(
                        base_dir=run_config["intermediate_storage"]["filesystem"]["config"][
                            "base_dir"
                        ],
                        tmp_dir=tmp_dir,
                        host_tmp_dir=host_tmp_dir,
                    )
                )
            else:
                run_config["intermediate_storage"]["filesystem"] = dict(
                    run_config["intermediate_storage"]["filesystem"] or {},
                    **{
                        "config": dict(
                            (
                                (
                                    run_config["intermediate_storage"].get("filesystem", {}) or {}
                                ).get("config", {})
                                or {}
                            ),
                            **{"base_dir": tmp_dir},
                        )
                    },
                )

        self.docker_conn_id_set = kwargs.get("docker_conn_id") is not None
        self.run_config = run_config
        self.pipeline_name = dagster_operator_parameters.pipeline_name
        self.pipeline_snapshot = dagster_operator_parameters.pipeline_snapshot
        self.execution_plan_snapshot = dagster_operator_parameters.execution_plan_snapshot
        self.parent_pipeline_snapshot = dagster_operator_parameters.parent_pipeline_snapshot
        self.mode = dagster_operator_parameters.mode
        self.step_keys = dagster_operator_parameters.step_keys
        self.recon_repo = dagster_operator_parameters.recon_repo
        self._run_id = None

        self.instance_ref = dagster_operator_parameters.instance_ref
        check.invariant(self.instance_ref)
        self.instance = DagsterInstance.from_ref(self.instance_ref)

        # These shenanigans are so we can override DockerOperator.get_hook in order to configure
        # a docker client using docker.from_env, rather than messing with the logic of
        # DockerOperator.execute
        if not self.docker_conn_id_set:
            try:
                from_env().version()
            except Exception:  # pylint: disable=broad-except
                pass
            else:
                kwargs["docker_conn_id"] = True

        if "environment" not in kwargs:
            kwargs["environment"] = get_aws_environment()

        super(DagsterDockerOperator, self).__init__(
            task_id=dagster_operator_parameters.task_id,
            dag=dagster_operator_parameters.dag,
            tmp_dir=tmp_dir,
            host_tmp_dir=host_tmp_dir,
            xcom_push=True,
            # We do this because log lines won't necessarily be emitted in order (!) -- so we can't
            # just check the last log line to see if it's JSON.
            xcom_all=True,
            *args,
            **kwargs,
        )

    @contextmanager
    def get_host_tmp_dir(self):
        yield self.host_tmp_dir

    def execute_raw(self, context):
        """Modified only to use the get_host_tmp_dir helper."""
        self.log.info("Starting docker container from image %s", self.image)

        tls_config = self.__get_tls_config()
        if self.docker_conn_id:
            self.cli = self.get_hook().get_conn()
        else:
            self.cli = APIClient(base_url=self.docker_url, version=self.api_version, tls=tls_config)

        if self.force_pull or len(self.cli.images(name=self.image)) == 0:
            self.log.info("Pulling docker image %s", self.image)
            for l in self.cli.pull(self.image, stream=True):
                output = seven.json.loads(l.decode("utf-8").strip())
                if "status" in output:
                    self.log.info("%s", output["status"])

        with self.get_host_tmp_dir() as host_tmp_dir:
            self.environment["AIRFLOW_TMP_DIR"] = self.tmp_dir
            self.volumes.append("{0}:{1}".format(host_tmp_dir, self.tmp_dir))

            self.container = self.cli.create_container(
                command=self.get_docker_command(context.get("ts")),
                environment=self.environment,
                host_config=self.cli.create_host_config(
                    auto_remove=self.auto_remove,
                    binds=self.volumes,
                    network_mode=self.network_mode,
                    shm_size=self.shm_size,
                    dns=self.dns,
                    dns_search=self.dns_search,
                    cpu_shares=int(round(self.cpus * 1024)),
                    mem_limit=self.mem_limit,
                ),
                image=self.image,
                user=self.user,
                working_dir=self.working_dir,
            )
            self.cli.start(self.container["Id"])

            res = []
            line = ""
            for new_line in self.cli.logs(
                container=self.container["Id"], stream=True, stdout=True, stderr=False
            ):
                line = new_line.strip()
                if hasattr(line, "decode"):
                    line = line.decode("utf-8")
                self.log.info(line)
                res.append(line)

            result = self.cli.wait(self.container["Id"])
            if result["StatusCode"] != 0:
                full_logs = self.cli.logs(container=self.container["Id"], stdout=True, stderr=True)

                raise AirflowException(
                    "docker container failed with result: {result} and logs: {logs}".format(
                        result=repr(result),
                        logs=full_logs,
                    )
                )

            if self.xcom_push_flag:
                # Try to avoid any kind of race condition?
                return res if self.xcom_all else str(line)

    # This is a class-private name on DockerOperator for no good reason --
    # all that the status quo does is inhibit extension of the class.
    # See https://issues.apache.org/jira/browse/AIRFLOW-3880
    def __get_tls_config(self):
        # pylint: disable=no-member
        return super(DagsterDockerOperator, self)._DockerOperator__get_tls_config()

    @property
    def run_id(self):
        if self._run_id is None:
            return ""
        else:
            return self._run_id

    def query(self, airflow_ts):
        check.opt_str_param(airflow_ts, "airflow_ts")

        recon_pipeline = self.recon_repo.get_reconstructable_pipeline(self.pipeline_name)

        input_json = serialize_dagster_namedtuple(
            ExecuteStepArgs(
                pipeline_origin=recon_pipeline.get_python_origin(),
                pipeline_run_id=self.run_id,
                instance_ref=self.instance_ref,
                step_keys_to_execute=self.step_keys,
            )
        )

        command = "dagster api execute_step {}".format(json.dumps(input_json))
        self.log.info("Executing: {command}\n".format(command=command))
        return command

    def get_docker_command(self, airflow_ts):
        """Deliberately renamed from get_command to avoid shadoowing the method of the base class"""
        check.opt_str_param(airflow_ts, "airflow_ts")

        if self.command is not None and self.command.strip().find("[") == 0:
            commands = ast.literal_eval(self.command)
        elif self.command is not None:
            commands = self.command
        else:
            commands = self.query(airflow_ts)
        return commands

    def get_hook(self):
        if self.docker_conn_id_set:
            return super(DagsterDockerOperator, self).get_hook()

        class _DummyHook:
            def get_conn(self):
                return from_env().api

        return _DummyHook()

    def _should_skip(self, pipeline_run):
        recon_pipeline = self.recon_repo.get_reconstructable_pipeline(self.pipeline_name)
        execution_plan = create_execution_plan(
            recon_pipeline.subset_for_execution_from_existing_pipeline(
                pipeline_run.solids_to_execute
            ),
            run_config=self.run_config,
            step_keys_to_execute=self.step_keys,
            mode=self.mode,
        )
        return should_skip_step(execution_plan, instance=self.instance, run_id=pipeline_run.run_id)

    def execute(self, context):
        if "run_id" in self.params:
            self._run_id = self.params["run_id"]
        elif "dag_run" in context and context["dag_run"] is not None:
            self._run_id = context["dag_run"].run_id

        try:
            tags = {AIRFLOW_EXECUTION_DATE_STR: context.get("ts")} if "ts" in context else {}

            pipeline_run = self.instance.register_managed_run(
                pipeline_name=self.pipeline_name,
                run_id=self.run_id,
                run_config=self.run_config,
                mode=self.mode,
                solids_to_execute=None,
                step_keys_to_execute=None,
                tags=tags,
                root_run_id=None,
                parent_run_id=None,
                pipeline_snapshot=self.pipeline_snapshot,
                execution_plan_snapshot=self.execution_plan_snapshot,
                parent_pipeline_snapshot=self.parent_pipeline_snapshot,
            )
            if self._should_skip(pipeline_run):
                raise AirflowSkipException(
                    "Dagster emitted skip event, skipping execution in Airflow"
                )

            res = self.execute_raw(context)
            self.log.info("Finished executing container.")

            if not res:
                raise AirflowException("Missing query response")

            try:
                events = [deserialize_json_to_dagster_namedtuple(line) for line in res if line]

            except Exception:  # pylint: disable=broad-except
                raise AirflowException(
                    "Could not parse response {response}".format(response=repr(res))
                )

            check_events_for_failures(events)
            check_events_for_skips(events)

            return events

        finally:
            self._run_id = None
