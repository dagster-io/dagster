'''The dagster-airflow Airflow plugin.

Place this file in your Airflow plugins directory (``$AIRFLOW_HOME/plugins``) to make
airflow.operators.dagster_plugin.DagsterOperator available.
'''
from __future__ import print_function

import ast
import errno
import json
import os
import sys

from contextlib import contextmanager
from copy import deepcopy
from textwrap import TextWrapper

from airflow.exceptions import AirflowException
from airflow.hooks.S3_hook import S3Hook
from airflow.operators.docker_operator import DockerOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.file import TemporaryDirectory
from docker import APIClient, from_env


if sys.version_info.major >= 3:
    from io import StringIO  # pylint:disable=import-error
else:
    from StringIO import StringIO  # pylint:disable=import-error

if sys.version_info.major >= 3:
    from json.decoder import JSONDecodeError  # pylint:disable=ungrouped-imports
else:
    JSONDecodeError = ValueError


# We don't use six here to avoid taking the dependency
STRING_TYPES = ("".__class__, u"".__class__)

# FIXME need the types and separate variables
DAGSTER_OPERATOR_COMMAND_TEMPLATE = '''-q '
{query}
'
'''.strip(
    '\n'
)

DOCKER_TEMPDIR = '/tmp/results'

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
    ... on PipelineConfigValidationInvalid {{
      pipeline {{
        name
      }}
      errors {{
        __typename
        message
        path
        reason
      }}
    }}
    ... on StartSubplanExecutionSuccess {{
      pipeline {{
        name
      }}
      hasFailures
      stepEvents {{
        step {{
          key
          solid {{
            name
          }}
          kind
        }}
        success
        __typename
        ... on SuccessfulStepOutputEvent {{
          step {{
            key
          }}
          success
          outputName
          valueRepr
        }}
        ... on StepFailureEvent {{
          step {{
            key
          }}
          success
          errorMessage
        }}
      }}
    }}
    ... on PythonError {{
        message
        stack
    }}
  }}
}}
'''.strip(
    '\n'
)

# TODO need better error handling for PythonError, StartSubplanExecutionInvalidStepsError,
# StartSubplanExecutionInvalidOutputError, ...?

LINE_LENGTH = 100


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# We include this directly to avoid taking the dependency on dagster
class IndentingBlockPrinter(object):
    def __init__(self, line_length=LINE_LENGTH, indent_level=4, current_indent=0):
        assert isinstance(current_indent, int)
        assert isinstance(indent_level, int)
        assert isinstance(indent_level, int)
        self.buffer = StringIO()
        self.line_length = line_length
        self.current_indent = current_indent
        self.indent_level = indent_level
        self.printer = lambda x: self.buffer.write(x + '\n')

        self._line_so_far = ''

    def append(self, text):
        assert isinstance(text, STRING_TYPES)
        self._line_so_far += text

    def line(self, text):
        assert isinstance(text, STRING_TYPES)
        self.printer(self.current_indent_str + self._line_so_far + text)
        self._line_so_far = ''

    @property
    def current_indent_str(self):
        return ' ' * self.current_indent

    def blank_line(self):
        assert not self._line_so_far, 'Cannot throw away appended strings by calling blank_line'
        self.printer('')

    def increase_indent(self):
        self.current_indent += self.indent_level

    def decrease_indent(self):
        if self.indent_level and self.current_indent <= 0:
            raise Exception('indent cannot be negative')
        self.current_indent -= self.indent_level

    @contextmanager
    def with_indent(self, text=None):
        if text is not None:
            self.line(text)
        self.increase_indent()
        yield
        self.decrease_indent()

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self.buffer.close()

    def block(self, text, prefix=''):
        '''Automagically wrap a block of text.'''
        assert isinstance(text, STRING_TYPES)
        wrapper = TextWrapper(
            width=self.line_length - len(self.current_indent_str),
            initial_indent=prefix,
            subsequent_indent=prefix,
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in wrapper.wrap(text):
            self.line(line)

    def comment(self, text):
        assert isinstance(text, STRING_TYPES)
        self.block(text, prefix='# ')

    def read(self):
        '''Get the value of the backing StringIO.'''
        return self.buffer.getvalue()


# not using abc because of six
class IntermediateValueManager(object):
    def init(self):
        raise NotImplementedError()

    def get_file(self, key, file_obj):
        raise NotImplementedError()

    def put_file(self, key, file_obj):
        raise NotImplementedError()


class S3IntermediateValueManager(IntermediateValueManager):
    def __init__(self, s3_hook, s3_bucket_name):
        self.s3_hook = s3_hook
        self.s3_bucket_name = s3_bucket_name

    def init(self):
        assert self.s3_hook.check_for_bucket(self.s3_bucket_name), (
            'If persist_intermediate_results_to_s3 is set, you must also set a valid '
            's3_bucket_name: could not find bucket \'{bucket_name}\'.'.format(
                bucket_name=self.s3_bucket_name
            )
        )

    def get_file(self, key, file_obj):
        return self.s3_hook.get_conn().download_fileobj(
            Bucket=self.s3_bucket_name, Key=key, Fileobj=file_obj
        )

    def put_file(self, key, file_obj):
        return self.s3_hook.get_conn().upload_fileobj(
            Bucket=self.s3_bucket_name, Key=key, Fileobj=file_obj
        )


# pylint: disable=len-as-condition
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

    # This is a class-private name on DockerOperator for no good reason --
    # all that the status quo does is inhibit extension of the class.
    # See https://issues.apache.org/jira/browse/AIRFLOW-3880
    def __get_tls_config(self):
        # pylint: disable=no-member
        return super(ModifiedDockerOperator, self)._DockerOperator__get_tls_config()


class DagsterOperator(ModifiedDockerOperator):
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
        step=None,
        config=None,
        pipeline_name=None,
        step_executions=None,
        docker_from_env=True,
        s3_conn_id=None,
        persist_intermediate_results_to_s3=False,
        s3_bucket_name=None,
        host_tmp_dir=None,
        *args,
        **kwargs
    ):
        self.step = step
        self.config = config
        self.pipeline_name = pipeline_name
        self._step_executions = step_executions
        self.docker_from_env = docker_from_env
        self.docker_conn_id_set = kwargs.get('docker_conn_id') is not None
        self.s3_conn_id = s3_conn_id
        self.persist_intermediate_results_to_s3 = persist_intermediate_results_to_s3
        self.s3_bucket_name = s3_bucket_name
        self.intermediate_value_manager = None
        self._run_id = None
        self._s3_hook = None

        if self.persist_intermediate_results_to_s3:
            assert isinstance(self.s3_bucket_name, STRING_TYPES), (
                'You must set a valid s3_bucket_name if persist_intermediate_results_to_s3 is set. '
                'Got: {value} of type {type_}.'.format(
                    value=self.s3_bucket_name, type_=type(self.s3_bucket_name)
                )
            )
            self.intermediate_value_manager = S3IntermediateValueManager(
                self.s3_hook, self.s3_bucket_name
            )
            self.intermediate_value_manager.init()

        # We don't use dagster.check here to avoid taking the dependency.
        for attr_ in ['config', 'pipeline_name']:
            assert isinstance(getattr(self, attr_), STRING_TYPES), (
                'Bad value for DagsterOperator {attr_}: expected a string and got {value} of '
                'type {type_}'.format(
                    attr_=attr_, value=getattr(self, attr_), type_=type(getattr(self, attr_))
                )
            )

        if self._step_executions is not None:
            assert isinstance(self._step_executions, list), (
                'Bad value for DagsterOperator step_executions: expected a list of dicts and got '
                '{value} of type {type_}'.format(
                    value=self._step_executions, type_=type(self._step_executions)
                )
            )

            for index, step_execution in enumerate(self._step_executions):
                assert isinstance(step_execution, dict), (
                    'Bad value for DagsterOperator step_executions: expected a list of dicts and '
                    'got {value} of type {type_} at index {index}'.format(
                        value=step_execution, type_=type(step_execution), index=index
                    )
                )

        # These shenanigans are so we can override DockerOperator.get_hook in order to configure
        # a docker client using docker.from_env, rather than messing with the logic of
        # DockerOperator.execute
        if not self.docker_conn_id_set:
            try:
                from_env().version()
            except:  # pylint: disable=bare-except
                pass
            else:
                kwargs['docker_conn_id'] = True

        assert isinstance(host_tmp_dir, STRING_TYPES), 'Must set a host_tmp_dir for DagsterOperator'
        # We do this because log lines won't necessarily be emitted in order (!) -- so we can't
        # just check the last log line to see if it's JSON.
        kwargs['xcom_all'] = True
        kwargs['host_tmp_dir'] = host_tmp_dir

        if 'network_mode' not in kwargs:
            # FIXME: this is not the best test to see if we're running on Docker for Mac
            kwargs['network_mode'] = 'host' if sys.platform != 'darwin' else 'bridge'
        super(DagsterOperator, self).__init__(*args, **kwargs)

    @property
    def run_id(self):
        if self._run_id is None:
            return ''
        else:
            return self._run_id

    @property
    def safe_run_id(self):
        '''Run_id with colons escaped so we can use it to name Docker volumes.'''
        return self.run_id.replace('_', '__').replace(':', '_')

    @property
    def s3_hook(self):
        if self._s3_hook:
            return self._s3_hook

        if self.s3_conn_id:
            self._s3_hook = S3Hook(aws_conn_id=self.s3_conn_id)
        else:
            self._s3_hook = S3Hook()

        return self._s3_hook

    @property
    def run_id_prefix(self):
        return (self.safe_run_id + '_') if self.safe_run_id else ''

    def get_step_executions(self, tmp=DOCKER_TEMPDIR, sep='/'):
        if not self._step_executions:
            return {}

        res = deepcopy(self._step_executions)
        for step_execution in res:
            for input_ in step_execution['inputs']:
                input_['key'] = input_['key'].format(
                    tmp=tmp, sep=sep, run_id_prefix=self.run_id_prefix
                )
            for output in step_execution['outputs']:
                output['key'] = output['key'].format(
                    tmp=tmp, sep=sep, run_id_prefix=self.run_id_prefix
                )
        return res

    @property
    def step_executions_query_fragment(self):  # pylint: disable=too-many-locals
        step_executions = self.get_step_executions()

        if not step_executions:
            return ''

        n_step_executions = len(step_executions)

        printer = IndentingBlockPrinter(indent_level=2)

        printer.line('[')
        with printer.with_indent():
            for idx, step_execution in enumerate(step_executions):
                inputs = step_execution['inputs']
                n_inputs = len(inputs)
                outputs = step_execution['outputs']
                n_outputs = len(outputs)
                step_key = step_execution['step_key']

                printer.line('{')
                with printer.with_indent():
                    printer.line('stepKey: "{step_key}"'.format(step_key=step_key))
                    printer.line('marshalledInputs: [')
                    with printer.with_indent():
                        for i, step_input in enumerate(inputs):
                            input_name = step_input['input_name']
                            key = step_input['key']

                            printer.line('{')
                            with printer.with_indent():
                                printer.line(
                                    'inputName: "{input_name}",'.format(input_name=input_name)
                                )
                                printer.line('key: "{key}"'.format(key=key))
                            printer.line('}}{comma}'.format(comma=',' if i < n_inputs - 1 else ''))
                    printer.line(']')
                    printer.line('marshalledOutputs: ')
                    with printer.with_indent():
                        for i, step_output in enumerate(outputs):
                            output_name = step_output['output_name']
                            key = step_output['key']
                            printer.line('{')
                            with printer.with_indent():
                                printer.line(
                                    'outputName: "{output_name}",'.format(output_name=output_name)
                                )
                                printer.line('key: "{key}"'.format(key=key))
                            printer.line('}}{comma}'.format(comma=',' if i < n_outputs - 1 else ''))
                printer.line('}}{comma}'.format(comma=',' if idx < n_step_executions - 1 else ''))
        printer.line(']')
        return printer.read()

    @property
    def query(self):
        return QUERY_TEMPLATE.format(
            config=self.config.strip('\n'),
            run_id=self.run_id,
            step_executions=self.step_executions_query_fragment,
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
        # govern whether intermediate result materializations get cleaned up or not. We could do
        # this by adding dummy start and end nodes to the scaffolded DAG that act as a context
        # manager for the run. This won't work when we're running on more than one worker though
        # -- here we'll need some kind of hook. S3 by default.
        mkdir_p(self.host_tmp_dir.format(safe_run_id=self.safe_run_id))
        yield self.host_tmp_dir.format(safe_run_id=self.safe_run_id)

    def execute(self, context):
        if 'dag_run' in context and context['dag_run'] is not None:
            self._run_id = context['dag_run'].run_id
        try:
            self.log.debug('Executing with query: {query}'.format(query=self.query))

            with self.get_host_tmp_dir() as tmp:
                step_executions = self.get_step_executions(tmp=tmp, sep=os.sep)

            if self.persist_intermediate_results_to_s3:
                # Some inputs may be coming from steps executing in this invocation
                seen = set()
                for step_execution in step_executions:
                    self.log.info(
                        'Processing step executions for step: {key}'.format(
                            key=step_execution['step_key']
                        )
                    )
                    for output in step_execution['outputs']:
                        seen.add(os.path.basename(output['key']))

                for step_execution in step_executions:
                    for input_ in step_execution['inputs']:
                        source_key = os.path.basename(input_['key'])
                        if source_key in seen:
                            self.log.info('Skipping input: {key}'.format(key=source_key))
                            continue

                        # Questionable
                        if os.path.isfile(input_['key']):
                            self.log.info(
                                'Skipping input: {key} (already present)'.format(key=source_key)
                            )
                            continue

                        self.log.info('Downloading key: {key}'.format(key=source_key))
                        with open(input_['key'], 'wb') as file_obj:
                            self.intermediate_value_manager.get_file(
                                key=source_key, file_obj=file_obj
                            )

            raw_res = super(DagsterOperator, self).execute(context)
            self.log.info('Finished executing container.')
            res = None

            # FIXME
            # Unfortunately, log lines don't necessarily come back in order...
            # This is error-prone, if something else logs JSON
            lines = list(reversed(raw_res.decode('utf-8').split('\n')))
            last_line = lines[0]

            for line in lines:
                try:
                    res = json.loads(line)
                    break
                # If we don't get a GraphQL response, check the next line
                except JSONDecodeError:
                    continue

            if res is None:
                raise AirflowException('Unhandled error type. Response: {}'.format(last_line))

            if res.get('errors'):
                raise AirflowException(
                    'Internal error in GraphQL request. Response: {}'.format(res)
                )

            res_type = res['data']['startSubplanExecution']['__typename']

            if res_type == 'PipelineConfigValidationInvalid':
                errors = [err['message'] for err in res['data']['startSubplanExecution']['errors']]
                raise AirflowException(
                    'Pipeline configuration invalid:\n{errors}'.format(errors='\n'.join(errors))
                )

            if res_type == 'StartSubplanExecutionSuccess':
                self.log.info('Subplan execution succeeded.')
                if res['data']['startSubplanExecution']['hasFailures']:
                    errors = [
                        step['errorMessage']
                        for step in res['data']['startSubplanExecution']['stepEvents']
                        if not step['success']
                    ]
                    raise AirflowException(
                        'Subplan execution failed:\n{errors}'.format(errors='\n'.join(errors))
                    )

                for step_execution in step_executions:
                    for output in step_execution['outputs']:
                        assert os.path.isfile(output['key'])

                if self.persist_intermediate_results_to_s3:
                    for step_execution in step_executions:
                        for output in step_execution['outputs']:
                            dest_key = os.path.basename(output['key'])
                            self.log.info('Uploading key: {key}'.format(key=dest_key))
                            with open(output['key'], 'rb') as file_obj:
                                self.intermediate_value_manager.put_file(
                                    key=dest_key, file_obj=file_obj
                                )

                return res

        finally:
            self._run_id = None

    # This is a class-private name on DockerOperator for no good reason --
    # all that the status quo does is inhibit extension of the class.
    # See https://issues.apache.org/jira/browse/AIRFLOW-3880
    def __get_tls_config(self):
        # pylint:disable=no-member
        return super(DagsterOperator, self)._ModifiedDockerOperator__get_tls_config()


class DagsterPlugin(AirflowPlugin):
    '''Dagster plugin for Apache Airflow.

    This plugin's only member is the DagsterOperator, which is intended to be used in
    autoscaffolded code created by dagster_airflow.scaffold_airflow_dag.
    '''

    name = 'dagster_plugin'
    operators = [DagsterOperator]
