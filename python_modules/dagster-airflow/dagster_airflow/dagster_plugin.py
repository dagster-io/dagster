'''The dagster-airflow Airflow plugin.

Place this file in your Airflow plugins directory (``$AIRFLOW_HOME/plugins``) to make
airflow.operators.dagster_plugin.DagsterOperator available.
'''
import ast
import json
import uuid

from contextlib import contextmanager

from airflow.exceptions import AirflowException
from airflow.operators.docker_operator import DockerOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.file import TemporaryDirectory
from docker import APIClient, from_env


# We don't use six here to avoid taking the dependency
STRING_TYPES = ("".__class__, u"".__class__)

# FIXME need the types and separate variables
DAGSTER_OPERATOR_COMMAND_TEMPLATE = '''-q '
{query}
'
'''.strip(
    '\n'
)

QUERY_TEMPLATE = '''
mutation(
  $config: PipelineConfig = {config},
  $stepExecutions: [StepExecution!] = {step_executions},
  $pipelineName: String = "{pipeline_name}",
  $runId: String = "{run_id}"
) {{
  startSubplanExecution(
    config: $config,
    executionMetadata: {{
      runId: $runId
    }},
    pipelineName: $pipelineName,
    stepExecutions: $stepExecutions,
  ) {{
    __typename
    ... on StartSubplanExecutionSuccess {{
      pipeline {{
        name
      }}
    }}
  }}
}}
'''.strip(
    '\n'
)

# FIXME need to support comprehensive error handling here

# ... on PipelineConfigValidationInvalid {
#     pipeline {
#         name
#     }
#     errors {
#         message
#         path
#         stack {
#         entries {
#             __typename
#             ... on EvaluationStackPathEntry {
#             field {
#                 name
#                 description
#                 configType {
#                 key
#                 name
#                 description
#                 }
#                 defaultValue
#                 isOptional
#             }
#             }
#         }
#         }
#         reason
#     }
#     }
#     ... on StartSubplanExecutionInvalidStepsError {
#     invalidStepKeys
#     }
#     ... on StartSubplanExecutionInvalidOutputError {
#     step {
#         key
#         inputs {
#         name
#         type {
#             key
#             name
#         }
#         }
#         outputs {
#         name
#         type {
#             key
#             name
#         }
#         }
#         solid {
#         name
#         definition {
#             name
#         }
#         inputs {
#             solid {
#             name
#             }
#             definition {
#             name
#             }
#         }
#         }
#         kind
#     }
#     }
# }
# }


class ModifiedDockerOperator(DockerOperator):
    """ModifiedDockerOperator supports host temporary directories on OSX.

    Incorporates https://github.com/apache/airflow/pull/4315/ and an implementation of
    https://issues.apache.org/jira/browse/AIRFLOW-3825.

    :param host_tmp_dir: Specify the location of the temporary directory on the host which will
        be mapped to tmp_dir. If not provided defaults to using the standard system temp directory.
    :type host_tmp_dir: str
    """

    def __init__(self, host_tmp_dir=None, **kwargs):
        self.host_tmp_dir = host_tmp_dir
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
                output = json.loads(l.decode('utf-8').strip())
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

            line = ''
            for line in self.cli.logs(container=self.container['Id'], stream=True):
                line = line.strip()
                if hasattr(line, 'decode'):
                    line = line.decode('utf-8')
                self.log.info(line)

            result = self.cli.wait(self.container['Id'])
            if result['StatusCode'] != 0:
                raise AirflowException('docker container failed: ' + repr(result))

            if self.xcom_push_flag:
                return self.cli.logs(container=self.container['Id']) if self.xcom_all else str(line)

    # We should open an Airflow issue so that this isn't a class-private name on DockerOperator --
    # all that the status quo does is inhibit extension of the class
    def __get_tls_config(self):
        return super(ModifiedDockerOperator, self)._DockerOperator__get_tls_config()


class DagsterOperator(ModifiedDockerOperator):
    '''Dagster operator for Apache Airflow.

    Wraps a modified DockerOperator incorporating https://github.com/apache/airflow/pull/4315.

    Additionally, if a Docker client can be initialized using docker.from_env, 
    Unlike the standard DockerOperator, this operator also supports config using docker.from_env,
    so it isn't necessary to explicitly set docker_url, tls_config, or api_version.

    '''

    def __init__(
        self,
        step=None,
        config=None,
        pipeline_name=None,
        step_executions=None,
        docker_from_env=True,
        s3_conn_id=None,
        persist_intermediate_results_to_s3=False,
        *args,
        **kwargs
    ):
        self.step = step
        self.config = config
        self.pipeline_name = pipeline_name
        self.step_executions = step_executions
        self.docker_from_env = docker_from_env
        self.docker_conn_id_set = kwargs.get('docker_conn_id') is not None
        self.s3_conn_id = s3_conn_id
        self.persist_intermediate_results_to_s3 = persist_intermediate_results_to_s3

        self._run_id = None

        # We don't use dagster.check here to avoid taking the dependency.
        for attr_ in ['config', 'pipeline_name', 'step_executions']:
            assert isinstance(getattr(self, attr_), STRING_TYPES), (
                'Bad value for DagsterOperator {attr_}: expected a string and got {value} of '
                'type {type_}'.format(
                    attr_=attr_, value=getattr(self, attr_), type_=type(getattr(self, attr_))
                )
            )

        # These shenanigans are so we can override DockerOperator.get_hook in order to configure
        # a docker client using docker.from_env, rather than messing with the logic of
        # DockerOperator.execute
        if not self.docker_conn_id_set:
            try:
                from_env().version()
            except Exception:
                pass
            else:
                kwargs['docker_conn_id'] = True

        super(DagsterOperator, self).__init__(*args, **kwargs)

    @property
    def query(self):
        return QUERY_TEMPLATE.format(
            config=self.config.strip('\n'),
            run_id=self._run_id,
            step_executions=self.step_executions.strip('\n'),
            pipeline_name=self.pipeline_name,
        )

    def get_command(self):
        if self.command is not None and self.command.strip().find('[') == 0:
            commands = ast.literal_eval(self.command)
        elif self.command is not None:
            commands = self.command
        else:
            commands = DAGSTER_OPERATOR_COMMAND_TEMPLATE.format(query=self.query)
        return commands

    def get_hook(self):
        if self.docker_conn_id_set:
            return super(DagsterOperator, self).get_hook()

        class _DummyHook(object):
            def get_conn(self):
                return from_env().api

        return _DummyHook()

    @contextmanager
    def get_host_tmp_dir(self):
        # FIXME: need to figure out what to do here. We probably want to provide some knobs to
        # govern whether intermediate result materializations get cleaned up or not.
        yield self.host_tmp_dir

    def execute(self, context):
        if 'dag_run' in context and context['dag_run'] is not None:
            self._run_id = context['dag_run'].run_id
        else:
            self._run_id = str(uuid.uuid4())
        try:
            # FIXME implement intermediate result persistence
            return super(DagsterOperator, self).execute(context)
        finally:
            self._run_id = None

    def __get_tls_config(self):
        return super(DagsterOperator, self)._ModifiedDockerOperator__get_tls_config()


class DagsterPlugin(AirflowPlugin):
    '''Dagster plugin for Apache Airflow.

    This plugin's only member is the DagsterOperator, which is intended to be used in
    autoscaffolded code created by dagster_airflow.scaffold_airflow_dag.
    '''

    name = 'dagster_plugin'
    operators = [DagsterOperator]
