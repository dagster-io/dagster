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
from textwrap import TextWrapper

from airflow.exceptions import AirflowException
from airflow.operators.docker_operator import DockerOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.file import TemporaryDirectory
from docker import APIClient, from_env


# We don't use seven to avoid taking the dependency
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

DEFAULT_ENVIRONMENT = {
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
}

# TODO need to enrich error handling as we enrich the ultimate union type for executePlan
QUERY_TEMPLATE = '''
mutation(
  $config: PipelineConfig = {config},
  $pipelineName: String = "{pipeline_name}",
  $runId: String = "{run_id}"
  $stepKeys: [String!] = {step_keys}
) {{
  executePlan(
    config: $config,
    executionMetadata: {{
      runId: $runId
    }},
    pipelineName: $pipelineName,
    stepKeys: $stepKeys,
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
    ... on PipelineNotFoundError {{
        message
        stack
        pipelineName
    }}
    ... on ExecutePlanSuccess {{
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
  }}
}}
'''.strip(
    '\n'
)

LINE_LENGTH = 100


# We include this directly to avoid taking the dependency on dagster
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


def parse_raw_res(raw_res):
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

    return (res, last_line)


def handle_errors(res, last_line):
    if res is None:
        raise AirflowException('Unhandled error type. Response: {}'.format(last_line))

    if res.get('errors'):
        raise AirflowException('Internal error in GraphQL request. Response: {}'.format(res))

    if not res.get('data', {}).get('executePlan', {}).get('__typename'):
        raise AirflowException('Unexpected response type. Response: {}'.format(res))


# pylint: disable=len-as-condition
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
        step_keys=None,
        s3_bucket_name=None,
        *args,
        **kwargs
    ):
        self.step = step
        self.config = config
        self.pipeline_name = pipeline_name
        self.step_keys = step_keys
        self.docker_conn_id_set = kwargs.get('docker_conn_id') is not None
        self.s3_bucket_name = s3_bucket_name
        self._run_id = None

        # We don't use dagster.check here to avoid taking the dependency.
        for attr_ in ['config', 'pipeline_name']:
            assert isinstance(getattr(self, attr_), STRING_TYPES), (
                'Bad value for DagsterOperator {attr_}: expected a string and got {value} of '
                'type {type_}'.format(
                    attr_=attr_, value=getattr(self, attr_), type_=type(getattr(self, attr_))
                )
            )

        if self.step_keys is None:
            self.step_keys = []

        assert isinstance(self.step_keys, list), (
            'Bad value for DagsterOperator step_keys: expected a list and got {value} of '
            'type {type_}'.format(value=self.step_keys, type_=type(self.step_keys))
        )

        bad_keys = []
        for ix, step_key in enumerate(self.step_keys):
            if not isinstance(step, STRING_TYPES):
                bad_keys.append((ix, step_key))
        assert (
            not bad_keys
        ), 'Bad values for DagsterOperator step_keys (expected only strings): {bad_values}'.format(
            bad_values=', '.join(
                [
                    '{value} of type {type_} at index {idx}'.format(
                        value=bad_key[1], type_=type(bad_key[1], idx=bad_key[0])
                    )
                    for bad_key in bad_keys
                ]
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

        # We do this because log lines won't necessarily be emitted in order (!) -- so we can't
        # just check the last log line to see if it's JSON.
        kwargs['xcom_all'] = True

        if 'network_mode' not in kwargs:
            # FIXME: this is not the best test to see if we're running on Docker for Mac
            kwargs['network_mode'] = 'host' if sys.platform != 'darwin' else 'bridge'

        if 'environment' not in kwargs:
            kwargs['environment'] = DEFAULT_ENVIRONMENT

        super(DagsterOperator, self).__init__(*args, **kwargs)

    @property
    def run_id(self):
        if self._run_id is None:
            return ''
        else:
            return self._run_id

    @property
    def query(self):
        step_keys = '[{quoted_step_keys}]'.format(
            quoted_step_keys=', '.join(
                ['"{step_key}"'.format(step_key=step_key) for step_key in self.step_keys]
            )
        )
        return QUERY_TEMPLATE.format(
            config=self.config.strip('\n'),
            run_id=self.run_id,
            step_keys=step_keys,
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

    def execute(self, context, **kwargs):
        if 'run_id' in self.params:
            self._run_id = self.params['run_id']
        elif 'dag_run' in context and context['dag_run'] is not None:
            self._run_id = context['dag_run'].run_id

        try:
            self.log.debug('Executing with query: {query}'.format(query=self.query))

            raw_res = super(DagsterOperator, self).execute(context)
            self.log.info('Finished executing container.')
            (res, last_line) = parse_raw_res(raw_res)

            handle_errors(res, last_line)

            res_data = res['data']['executePlan']

            res_type = res_data['__typename']

            if res_type == 'PipelineConfigValidationInvalid':
                errors = [err['message'] for err in res_data['errors']]
                raise AirflowException(
                    'Pipeline configuration invalid:\n{errors}'.format(errors='\n'.join(errors))
                )

            if res_type == 'PipelineNotFoundError':
                raise AirflowException(
                    'Pipeline {pipeline_name} not found: {message}:\n{stack_entries}'.format(
                        pipeline_name=res_data['pipelineName'],
                        message=res_data['message'],
                        stack_entries='\n'.join(res_data['stack']),
                    )
                )

            if res_type == 'ExecutePlanSuccess':
                self.log.info('Plan execution succeeded.')
                if res_data['hasFailures']:
                    errors = [
                        step['errorMessage']
                        for step in res_data['stepEvents']
                        if not step['success']
                    ]
                    raise AirflowException(
                        'Subplan execution failed:\n{errors}'.format(errors='\n'.join(errors))
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
