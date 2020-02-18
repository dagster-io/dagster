import ast
import sys
import warnings
from contextlib import contextmanager

from airflow.exceptions import AirflowException
from airflow.utils.file import TemporaryDirectory
from dagster_airflow.vendor.docker_operator import DockerOperator
from dagster_graphql.client.query import RAW_EXECUTE_PLAN_MUTATION
from docker import APIClient, from_env

from dagster import check, seven
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils.error import serializable_error_info_from_exc_info

from .util import (
    check_events_for_failures,
    check_events_for_skips,
    construct_variables,
    get_aws_environment,
    parse_raw_res,
)

DOCKER_TEMPDIR = '/tmp'


class ModifiedDockerOperator(DockerOperator):
    """ModifiedDockerOperator supports host temporary directories on OSX.

    Incorporates https://github.com/apache/airflow/pull/4315/ and an implementation of
    https://issues.apache.org/jira/browse/AIRFLOW-3825.

    :param host_tmp_dir: Specify the location of the temporary directory on the host which will
        be mapped to tmp_dir. If not provided defaults to using the standard system temp directory.
    :type host_tmp_dir: str
    """

    def __init__(self, host_tmp_dir='/tmp', **kwargs):
        self.host_tmp_dir = host_tmp_dir
        kwargs['xcom_push'] = True
        super(ModifiedDockerOperator, self).__init__(**kwargs)

    @contextmanager
    def get_host_tmp_dir(self):
        '''Abstracts the tempdir context manager so that this can be overridden.'''
        with TemporaryDirectory(prefix='airflowtmp', dir=self.host_tmp_dir) as tmp_dir:
            yield tmp_dir

    def execute(self, context):
        '''Modified only to use the get_host_tmp_dir helper.'''
        self.log.info('Starting docker container from image %s', self.image)

        tls_config = self.__get_tls_config()
        if self.docker_conn_id:
            self.cli = self.get_hook().get_conn()
        else:
            self.cli = APIClient(base_url=self.docker_url, version=self.api_version, tls=tls_config)

        if self.force_pull or len(self.cli.images(name=self.image)) == 0:
            self.log.info('Pulling docker image %s', self.image)
            for l in self.cli.pull(self.image, stream=True):
                output = seven.json.loads(l.decode('utf-8').strip())
                if 'status' in output:
                    self.log.info("%s", output['status'])

        with self.get_host_tmp_dir() as host_tmp_dir:
            self.environment['AIRFLOW_TMP_DIR'] = self.tmp_dir
            self.volumes.append('{0}:{1}'.format(host_tmp_dir, self.tmp_dir))

            self.container = self.cli.create_container(
                command=self.get_command(),
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
            self.cli.start(self.container['Id'])

            res = []
            line = ''
            for new_line in self.cli.logs(container=self.container['Id'], stream=True):
                line = new_line.strip()
                if hasattr(line, 'decode'):
                    line = line.decode('utf-8')
                self.log.info(line)
                res.append(line)

            result = self.cli.wait(self.container['Id'])
            if result['StatusCode'] != 0:
                raise AirflowException(
                    'docker container failed with result: {result} and logs: {logs}'.format(
                        result=repr(result), logs='\n'.join(res)
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
        return super(ModifiedDockerOperator, self)._DockerOperator__get_tls_config()


class DagsterDockerOperator(ModifiedDockerOperator):
    '''Dagster operator for Apache Airflow.

    Wraps a modified DockerOperator incorporating https://github.com/apache/airflow/pull/4315.

    Additionally, if a Docker client can be initialized using docker.from_env,
    Unlike the standard DockerOperator, this operator also supports config using docker.from_env,
    so it isn't necessary to explicitly set docker_url, tls_config, or api_version.

    '''

    # py2 compat
    # pylint: disable=keyword-arg-before-vararg
    def __init__(
        self,
        task_id,
        pipeline_name,
        mode,
        environment_dict=None,
        step_keys=None,
        dag=None,
        instance_ref=None,
        *args,
        **kwargs
    ):
        check.str_param(pipeline_name, 'pipeline_name')
        step_keys = check.opt_list_param(step_keys, 'step_keys', of_type=str)
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
        check.opt_inst_param(instance_ref, 'instance_ref', InstanceRef)

        tmp_dir = kwargs.pop('tmp_dir', DOCKER_TEMPDIR)
        host_tmp_dir = kwargs.pop('host_tmp_dir', seven.get_system_temp_directory())

        if not environment_dict.get('storage'):
            raise AirflowException(
                'No storage config found -- must configure storage for '
                'the DagsterDockerOperator. Ex.: \n'
                'storage:\n'
                '  filesystem:\n'
                '    config:'
                '      base_dir: \'/some/shared/volume/mount/special_place\''
                '\n\n --or--\n\n'
                'storage:\n'
                '  s3:\n'
                '    s3_bucket: \'my-s3-bucket\'\n'
                '\n\n --or--\n\n'
                'storage:\n'
                '  gcs:\n'
                '    gcs_bucket: \'my-gcs-bucket\'\n'
            )

        if 'filesystem' in environment_dict['storage']:
            if (
                'config' in (environment_dict['storage'].get('filesystem', {}) or {})
                and 'base_dir'
                in (
                    (environment_dict['storage'].get('filesystem', {}) or {}).get('config', {})
                    or {}
                )
                and environment_dict['storage']['filesystem']['config']['base_dir'] != tmp_dir
            ):
                warnings.warn(
                    'Found base_dir \'{base_dir}\' set in filesystem storage config, which was not '
                    'the tmp_dir we expected (\'{tmp_dir}\', mounting host_tmp_dir '
                    '\'{host_tmp_dir}\' from the host). We assume you know what you are doing, but '
                    'if you are having trouble executing containerized workloads, this may be the '
                    'issue'.format(
                        base_dir=environment_dict['storage']['filesystem']['config']['base_dir'],
                        tmp_dir=tmp_dir,
                        host_tmp_dir=host_tmp_dir,
                    )
                )
            else:
                environment_dict['storage']['filesystem'] = dict(
                    environment_dict['storage']['filesystem'] or {},
                    **{
                        'config': dict(
                            (
                                (environment_dict['storage'].get('filesystem', {}) or {}).get(
                                    'config', {}
                                )
                                or {}
                            ),
                            **{'base_dir': tmp_dir}
                        )
                    }
                )

        self.docker_conn_id_set = kwargs.get('docker_conn_id') is not None
        self.environment_dict = environment_dict
        self.pipeline_name = pipeline_name
        self.mode = mode
        self.step_keys = step_keys
        self._run_id = None
        # self.instance might be None in, for instance, a unit test setting where the operator
        # was being directly instantiated without passing through make_airflow_dag
        self.instance = DagsterInstance.from_ref(instance_ref) if instance_ref else None

        # These shenanigans are so we can override DockerOperator.get_hook in order to configure
        # a docker client using docker.from_env, rather than messing with the logic of
        # DockerOperator.execute
        if not self.docker_conn_id_set:
            try:
                from_env().version()
            except Exception:  # pylint: disable=broad-except
                pass
            else:
                kwargs['docker_conn_id'] = True

        # We do this because log lines won't necessarily be emitted in order (!) -- so we can't
        # just check the last log line to see if it's JSON.
        kwargs['xcom_all'] = True

        # Store Airflow DAG run timestamp so that we can pass along via execution metadata
        self.airflow_ts = kwargs.get('ts')

        if 'environment' not in kwargs:
            kwargs['environment'] = get_aws_environment()

        super(DagsterDockerOperator, self).__init__(
            task_id=task_id, dag=dag, tmp_dir=tmp_dir, host_tmp_dir=host_tmp_dir, *args, **kwargs
        )

    @property
    def run_id(self):
        if self._run_id is None:
            return ''
        else:
            return self._run_id

    @property
    def query(self):
        # TODO: https://github.com/dagster-io/dagster/issues/1342
        redacted = construct_variables(
            self.mode, 'REDACTED', self.pipeline_name, self.run_id, self.airflow_ts, self.step_keys
        )
        self.log.info(
            'Executing GraphQL query: {query}\n'.format(query=RAW_EXECUTE_PLAN_MUTATION)
            + 'with variables:\n'
            + seven.json.dumps(redacted, indent=2)
        )

        variables = construct_variables(
            self.mode,
            self.environment_dict,
            self.pipeline_name,
            self.run_id,
            self.airflow_ts,
            self.step_keys,
        )

        return 'dagster-graphql -v \'{variables}\' -t \'{query}\''.format(
            variables=seven.json.dumps(variables), query=RAW_EXECUTE_PLAN_MUTATION
        )

    def get_command(self):
        if self.command is not None and self.command.strip().find('[') == 0:
            commands = ast.literal_eval(self.command)
        elif self.command is not None:
            commands = self.command
        else:
            commands = self.query
        return commands

    def get_hook(self):
        if self.docker_conn_id_set:
            return super(DagsterDockerOperator, self).get_hook()

        class _DummyHook(object):
            def get_conn(self):
                return from_env().api

        return _DummyHook()

    def execute(self, context):
        try:
            from dagster_graphql.client.mutations import (
                DagsterGraphQLClientError,
                handle_execution_errors,
                handle_execute_plan_result_raw,
            )

        except ImportError:
            raise AirflowException(
                'To use the DagsterDockerOperator, dagster and dagster_graphql must be installed '
                'in your Airflow environment.'
            )

        if 'run_id' in self.params:
            self._run_id = self.params['run_id']
        elif 'dag_run' in context and context['dag_run'] is not None:
            self._run_id = context['dag_run'].run_id

        pipeline_run = PipelineRun(
            pipeline_name=self.pipeline_name,
            run_id=self.run_id,
            environment_dict=self.environment_dict,
            mode=self.mode,
            selector=ExecutionSelector(self.pipeline_name),
            step_keys_to_execute=None,
            tags=None,
            status=PipelineRunStatus.MANAGED,
        )
        try:
            if self.instance:
                self.instance.get_or_create_run(pipeline_run)

            raw_res = super(DagsterDockerOperator, self).execute(context)
            self.log.info('Finished executing container.')

            res = parse_raw_res(raw_res)

            try:
                handle_execution_errors(res, 'executePlan')
            except DagsterGraphQLClientError as err:
                if self.instance:
                    self.instance.report_engine_event(
                        self.__class__,
                        str(err),
                        pipeline_run,
                        EngineEventData.engine_error(
                            serializable_error_info_from_exc_info(sys.exc_info())
                        ),
                    )
                raise

            events = handle_execute_plan_result_raw(res)

            if self.instance:
                for event in events:
                    self.instance.handle_new_event(event)

            events = [e.dagster_event for e in events]
            check_events_for_failures(events)
            check_events_for_skips(events)

            return events

        finally:
            self._run_id = None

    # This is a class-private name on DockerOperator for no good reason --
    # all that the status quo does is inhibit extension of the class.
    # See https://issues.apache.org/jira/browse/AIRFLOW-3880
    def __get_tls_config(self):
        # pylint:disable=no-member
        return super(DagsterDockerOperator, self)._ModifiedDockerOperator__get_tls_config()

    @contextmanager
    def get_host_tmp_dir(self):
        yield self.host_tmp_dir
