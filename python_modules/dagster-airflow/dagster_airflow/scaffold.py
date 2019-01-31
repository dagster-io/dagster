'''Scaffolding machinery for dagster-airflow.

Entrypoint is scaffold_airflow_dag, which consumes a pipeline definition and a config, and
generates an Airflow DAG definition each of whose nodes corresponds to one step of the execution
plan.
'''

import os

from datetime import datetime, timedelta

from six import string_types
from yaml import dump

from dagster import check, PipelineDefinition
from dagster.core.execution import create_execution_plan

from .utils import IndentingBlockPrinter


DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(0, 300),
}


def _normalize_key(key):
    '''We need to make sure task ids play nicely with Airflow.'''
    return key.replace('_', '__').replace('.', '_')


def _is_py(path):
    '''We need to make sure we are writing out Python files.'''
    return path.split('.')[-1] == 'py'


def _bad_import(path):
    '''We need to make sure our relative import will work.'''
    return '.' in os.path.basename(path)[:-3]


def _split_lines(lines):
    '''Fancy utility adds a trailing comma to the last line of output.'''
    return (lines.strip('\n') + ',').split('\n')


def _key_for_marshalled_result(step_key, result_name):
    '''Standardizes keys for marshalled inputs and outputs.'''
    return (
        '/tmp/results/' + _normalize_key(step_key) + '___' + _normalize_key(result_name) + '.pickle'
    )


def _scaffold_marshalled_inputs_for_step(step):
    '''Generate the marshalled input block for our scaffolding.'''
    printer = IndentingBlockPrinter(indent_level=2)
    printer.line('[')
    with printer.with_indent():
        for step_input in step.step_inputs:
            printer.line('{{')
            with printer.with_indent():
                printer.line('inputName: "{input_name}",'.format(input_name=step_input.name))
                printer.line(
                    'key: "{key}"'.format(
                        key=_key_for_marshalled_result(
                            step_input.prev_output_handle.step.key,
                            step_input.prev_output_handle.output_name,
                        )
                    )
                )
            printer.line('}}')
    printer.line(']')

    return printer.read()


def _scaffold_marshalled_outputs_for_step(step):
    '''Generate the marshalled output block for our scaffolding.'''
    printer = IndentingBlockPrinter(indent_level=2)
    printer.line('[')
    with printer.with_indent():
        for step_output in step.step_outputs:
            printer.line('{{')
            with printer.with_indent():
                printer.line('outputName: "{output_name}",'.format(output_name=step_output.name))
                printer.line(
                    'key: "{key}"'.format(
                        key=_key_for_marshalled_result(step.key, step_output.name)
                    )
                )
            printer.line('}}')
    printer.line(']')

    return printer.read()


def _format_config(config):
    '''This recursive descent thing formats a config dict for GraphQL.'''

    def _format_config_subdict(config, current_indent=0):
        check.dict_param(config, 'config', key_type=str)

        printer = IndentingBlockPrinter(indent_level=2, current_indent=current_indent)
        printer.line('{')

        n_elements = len(config)
        for i, key in enumerate(sorted(config, key=lambda x: x[0])):
            value = config[key]
            with printer.with_indent():
                formatted_value = (
                    _format_config_item(value, current_indent=printer.current_indent)
                    .lstrip(' ')
                    .rstrip('\n')
                )
                printer.line(
                    '{key}: {formatted_value}{comma}'.format(
                        key=key,
                        formatted_value=formatted_value,
                        comma=',' if i != n_elements - 1 else '',
                    )
                )
        printer.line('}')

        return printer.read()

    def _format_config_sublist(config, current_indent=0):
        printer = IndentingBlockPrinter(indent_level=2, current_indent=current_indent)
        printer.line('[')

        n_elements = len(config)
        for i in range(len(config)):
            value = config[i]
            with printer.with_indent():
                formatted_value = (
                    _format_config_item(value, current_indent=printer.current_indent)
                    .lstrip(' ')
                    .rstrip('\n')
                )
                printer.line(
                    '{formatted_value}{comma}'.format(
                        formatted_value=formatted_value, comma=',' if i != n_elements - 1 else ''
                    )
                )
        printer.line(']')

        return printer.read()

    def _format_config_item(config, current_indent=0):
        printer = IndentingBlockPrinter(indent_level=2, current_indent=current_indent)

        if isinstance(config, dict):
            return _format_config_subdict(config, printer.current_indent)
        elif isinstance(config, list):
            return _format_config_sublist(config, printer.current_indent)
        else:
            return repr(config).replace('\'', '"')

    check.dict_param(config, 'config', key_type=str)
    if not isinstance(config, dict):
        check.failed('Expected a dict to format as config, got: {item}'.format(item=repr(config)))

    return _format_config_subdict(config)


def _scaffold_query_for_step(pipeline_name, step):
    marshalled_inputs = _scaffold_marshalled_inputs_for_step(step)
    marshalled_outputs = _scaffold_marshalled_outputs_for_step(step)

    printer = IndentingBlockPrinter(indent_level=2)

    printer.line('mutation {{')
    with printer.with_indent():
        printer.line('startSubplanExecution(')
        with printer.with_indent():
            printer.line('config: {config},')
            printer.line('executionMetadata: {{')
            with printer.with_indent():
                printer.line('runId: "testRun"')  # FIXME need to see if we can thread this through
            printer.line('}},')
            printer.line('pipelineName: "{pipeline_name}",'.format(pipeline_name=pipeline_name))
            printer.line('stepExecutions: [')
            with printer.with_indent():
                printer.line('{{')
                with printer.with_indent():
                    printer.line('stepKey: "{step_key}"'.format(step_key=step.key))
                    printer.line('marshalledInputs: ')
                    for line in (marshalled_inputs.strip('\n') + ',').split('\n'):
                        printer.line(line)
                    printer.line('marshalledOutputs: ')
                    for line in (marshalled_outputs.strip('\n') + ',').split('\n'):
                        printer.line(line)
                printer.line('}}')
            printer.line('],')
        printer.line(') {{')
        with printer.with_indent():
            printer.line('__typename')
            printer.line('... on StartSubplanExecutionSuccess {{')
            with printer.with_indent():
                printer.line('pipeline {{')
                with printer.with_indent():
                    printer.line('name')
                printer.line('}}')
            printer.line('}}')
        printer.line('}}')
    printer.line('}}')
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
    return printer.read()


def _make_editable_scaffold(
    pipeline_name, pipeline_description, env_config, static_scaffold, default_args
):

    pipeline_description = '***Autogenerated by dagster-airflow***' + (
        '''

    {pipeline_description}
    '''.format(
            pipeline_description=pipeline_description
        )
        if pipeline_description
        else ''
    )

    with IndentingBlockPrinter() as printer:
        printer.block(
            '\'\'\'Editable scaffolding autogenerated by dagster-airflow from pipeline '
            '{pipeline_name} with config:'.format(pipeline_name=pipeline_name)
        )
        printer.blank_line()

        with printer.with_indent():
            for line in dump(env_config).split('\n'):
                printer.line(line)
        printer.blank_line()

        printer.block(
            'By convention, users should attempt to isolate post-codegen changes and '
            'customizations to this "editable" file, rather than changing the definitions in the '
            '"static" {static_scaffold}.py file. Please let us know if you are encountering use '
            'cases where it is necessary to make changes to the static file.'.format(
                static_scaffold=static_scaffold
            )
        )
        printer.line('\'\'\'')
        printer.blank_line()

        printer.line('import datetime')
        printer.blank_line()

        printer.line(
            'from {static_scaffold} import make_dag'.format(static_scaffold=static_scaffold)
        )
        printer.blank_line()

        printer.comment(
            'Arguments to be passed to the ``default_args`` parameter of the ``airflow.DAG`` '
            'constructor.You can override these with values of your choice.'
        )
        printer.line('DEFAULT_ARGS = {')
        with printer.with_indent():
            for key, value in sorted(default_args.items(), key=lambda x: x[0]):
                printer.line('\'{key}\': {value_repr},'.format(key=key, value_repr=repr(value)))
        printer.line('}')
        printer.blank_line()

        printer.comment(
            'Any additional keyword arguments to be passed to the ``airflow.DAG`` constructor. '
            'You can override these with values of your choice.'
        )
        printer.line('DAG_KWARGS = {}')
        printer.blank_line()

        printer.comment(
            'The name of the autogenerated DAG. By default, this is just the name of the Dagster '
            'pipeline from which the Airflow DAG was generated ({pipeline_name}). You may want to '
            'override this if, for instance, you want to schedule multiple DAGs corresponding to '
            'different configurations of the same Dagster pipeline.'.format(
                pipeline_name=pipeline_name
            )
        )
        printer.line('DAG_ID = \'{pipeline_name}\''.format(pipeline_name=pipeline_name))
        printer.blank_line()

        printer.comment(
            'The description of the autogenerated DAG. By default, this is the description of the '
            'Dagster pipeline from which the Airflow DAG was generated. You may want to override '
            'this, as with the DAG_ID parameter.'
        )
        printer.line(
            'DAG_DESCRIPTION = \'\'\'{pipeline_description}\'\'\''.format(
                pipeline_description=pipeline_description
            )
        )
        printer.blank_line()

        printer.comment(
            'Additional arguments, if any, to pass to the underlying '
            '``dagster_airflow.dagster_plugin.ModifiedDockerOperator`` constructor. Set these if, '
            'for instance, you need to set special TLS parameters.'
        )
        printer.line('MODIFIED_DOCKER_OPERATOR_KWARGS = {}')
        printer.blank_line()

        printer.comment(
            'Set your S3 connection id here, if you do not want to use the default ``aws_default`` '
            'connection.'
        )
        printer.line('S3_CONN_ID = \'aws_default\'')
        printer.blank_line()

        printer.comment('Set the host directory to mount into /tmp/results on the containers.')
        printer.line('HOST_TMP_DIR = \'/tmp/results\'')
        printer.blank_line()

        printer.line('dag = make_dag(')
        with printer.with_indent():
            printer.line('dag_id=DAG_ID,')
            printer.line('dag_description=DAG_DESCRIPTION,')
            printer.line('dag_kwargs=dict(default_args=DEFAULT_ARGS, **DAG_KWARGS),')
            printer.line('s3_conn_id=S3_CONN_ID,')
            printer.line('modified_docker_operator_kwargs=MODIFIED_DOCKER_OPERATOR_KWARGS,')
            printer.line('host_tmp_dir=HOST_TMP_DIR,')
        printer.line(')')

        return printer.read()


def _make_static_scaffold(pipeline_name, env_config, execution_plan, image, editable_scaffold):
    with IndentingBlockPrinter() as printer:
        printer.block(
            '\'\'\'Static scaffolding autogenerated by dagster-airflow from pipeline '
            '{pipeline_name} with config:'.format(pipeline_name=pipeline_name)
        )
        printer.blank_line()

        with printer.with_indent():
            for line in dump(env_config).split('\n'):
                printer.line(line)
        printer.blank_line()

        printer.block(
            'By convention, users should attempt to isolate post-codegen changes and '
            'customizations to the "editable" {editable_scaffold}.py file, rather than changing '
            'the definitions in this "static" file. Please let us know if you are encountering '
            'use cases where it is necessary to make changes to the static file.'.format(
                editable_scaffold=editable_scaffold
            )
        )
        printer.line('\'\'\'')
        printer.blank_line()

        printer.line('from airflow import DAG')
        printer.line('from airflow.operators.dagster_plugin import DagsterOperator')
        printer.blank_line()
        printer.blank_line()

        printer.line('CONFIG = \'\'\'')
        with printer.with_indent():
            for line in _format_config(env_config).strip('\n').split('\n'):
                printer.line(line)
        printer.line('\'\'\'')
        printer.blank_line()
        printer.blank_line()

        printer.line('def make_dag(')
        with printer.with_indent():
            printer.line('dag_id,')
            printer.line('dag_description,')
            printer.line('dag_kwargs,')
            printer.line('s3_conn_id,')
            printer.line('modified_docker_operator_kwargs,')
            printer.line('host_tmp_dir')
        printer.line('):')
        with printer.with_indent():
            printer.line('dag = DAG(')
            with printer.with_indent():
                printer.line('dag_id=dag_id,')
                printer.line('description=dag_description,')
                printer.line('**dag_kwargs,')
            printer.line(')')
            printer.blank_line()

            for step in execution_plan.topological_steps():
                step_key = step.key
                airflow_step_key = _normalize_key(step_key)

                query = _scaffold_query_for_step(pipeline_name, step)

                printer.line(
                    '{airflow_step_key}_task = DagsterOperator('.format(
                        airflow_step_key=airflow_step_key
                    )
                )
                with printer.with_indent():
                    printer.line('step=\'{step_key}\','.format(step_key=step_key))
                    printer.line('config=CONFIG,')
                    printer.line('dag=dag,')
                    printer.line('tmp_dir=\'/tmp/results\',')
                    printer.line('host_tmp_dir=host_tmp_dir,')
                    printer.line('image=\'{image}\','.format(image=image))
                    printer.line(
                        'task_id=\'{airflow_step_key}\','.format(airflow_step_key=airflow_step_key)
                    )
                    printer.line('s3_conn_id=s3_conn_id,')
                    printer.line('command=\'\'\'-q \'')
                    with printer.with_indent():
                        for line in query.split('\n')[:-1]:
                            printer.line(line)
                        printer.line('\'')
                    printer.line('\'\'\'.format(config=CONFIG.strip(\'\\n\')),')
                printer.line(')')
                printer.blank_line()

            for step in execution_plan.topological_steps():
                for step_input in step.step_inputs:
                    prev_airflow_step_key = _normalize_key(step_input.prev_output_handle.step.key)
                    airflow_step_key = _normalize_key(step.key)
                    printer.line(
                        '{prev_airflow_step_key}_task.set_downstream({airflow_step_key}_task)'.format(
                            prev_airflow_step_key=prev_airflow_step_key,
                            airflow_step_key=airflow_step_key,
                        )
                    )
            printer.blank_line()
            printer.line('return dag')

        return printer.read()


def scaffold_airflow_dag(pipeline, env_config, image, output_path=None, dag_kwargs=None):
    '''Scaffold a new Airflow DAG based on a PipelineDefinition and config.

    Creates an "editable" scaffold (intended for end user modification) and a "static" scaffold.
    The editable scaffold imports the static scaffold and defines the Airflow DAG. As a rule, both
    scaffold files need to be present in your Airflow DAG directory (by default, this is
    $AIRFLOW_HOME/dags)in order to be correctly parsed by Airflow.

    Note that an Airflow DAG corresponds to a Dagster execution plan, since many different
    execution plans may be created when a PipelineDefinition is parametrized by various config
    values. You may want to create multiple Airflow DAGs corresponding to, e.g., test and
    production configs of your Dagster pipelines.

    Parameters:
        pipeline (dagster.PipelineDefinition): Pipeline to use to construct the Airflow DAG.
        env_config (dict): The config to use to construct the Airflow DAG.
        image (str): The name of the Docker image in which your pipeline has been containerized.
        output_path (Union[Tuple[str, str], str, None]): Optionally specify the path at which to
            write the scaffolded files. If this parameter is a tuple of absolute paths, the static
            scaffold will be written to the first member of the tuple and the editable scaffold
            will be written to the second member of the tuple. If this parameter is a path to a
            directory, the scaffold files will be written to that directory as
            '{pipeline_name}_static__scaffold.py' and '{pipeline_name}_editable__scaffold.py'
            respectively. If this parameter is None, the scaffolds will be written to the present
            working directory.
        dag_kwargs (dict, optional): Any additional keyword arguments to pass to the ``airflow.DAG``
            constructor. If `dag_kwargs.default_args` is set, values set there will smash the
            values in ``dagster_airflow.scaffold.DEFAULT_ARGS``. Default: None.
    
    Returns:
        (str, str): Paths to the static and editable scaffold files.
    '''
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)
    check.opt_dict_param(env_config, 'env_config', key_type=str)
    dag_kwargs = check.opt_dict_param(dag_kwargs, 'dag_kwargs', key_type=str)

    pipeline_name = pipeline.name
    pipeline_description = pipeline.description

    if output_path is None:
        static_path = os.path.join(
            os.getcwd(), '{pipeline_name}_static__scaffold.py'.format(pipeline_name=pipeline_name)
        )
        editable_path = os.path.join(
            os.getcwd(), '{pipeline_name}_editable__scaffold.py'.format(pipeline_name=pipeline_name)
        )
    elif isinstance(output_path, tuple):
        if not len(output_path) == 2:
            check.failed(
                'output_path must be a tuple(str, str), str, or None. Got a tuple with bad '
                'length {length}'.format(length=len(output_path))
            )

        if not os.path.isabs(output_path[0]) or not os.path.isabs(output_path[1]):
            check.failed(
                'Bad value for output_path: expected a tuple of absolute paths, but got '
                '({path_0}, {path_1}).'.format(path_0=output_path[0], path_1=output_path[1])
            )

        if not _is_py(output_path[0]) or not _is_py(output_path[1]):
            check.failed(
                'Bad value for output_path: expected a tuple of absolute paths to python files '
                '(*.py), but got ({path_0}, {path_1}).'.format(
                    path_0=output_path[0], path_1=output_path[1]
                )
            )

        if _bad_import(output_path[0]) or _bad_import(output_path[1]):
            check.failed(
                'Bad value for output_path: no dots permitted in filenames. Got: '
                '({path_0}, {path_1}).'.format(path_0=output_path[0], path_1=output_path[1])
            )

        static_path, editable_path = output_path
    elif isinstance(output_path, string_types):
        if not os.path.isabs(output_path):
            check.failed(
                'Bad value for output_path: expected an absolute path, but got {path}.'.format(
                    path=output_path
                )
            )

        if not os.path.isdir(output_path):
            check.failed(
                'Bad value for output_path: No directory found at {output_path}'.format(
                    output_path=output_path
                )
            )

        static_path = os.path.join(
            output_path, '{pipeline_name}_static__scaffold.py'.format(pipeline_name=pipeline_name)
        )
        editable_path = os.path.join(
            output_path, '{pipeline_name}_editable__scaffold.py'.format(pipeline_name=pipeline_name)
        )
    else:
        check.failed(
            'output_path must be a tuple(str, str), str, or None. Got: {type_}'.format(
                type_=type(output_path)
            )
        )

    execution_plan = create_execution_plan(pipeline, env_config)

    default_args = dict(
        dict(DEFAULT_ARGS, start_date=datetime.utcnow()), **(dag_kwargs.pop('default_args', {}))
    )

    editable_scaffold_module_name = os.path.basename(editable_path).split('.')[-2]
    static_scaffold_module_name = os.path.basename(static_path).split('.')[-2]

    static_scaffold = _make_static_scaffold(
        pipeline_name=pipeline_name,
        env_config=env_config,
        execution_plan=execution_plan,
        image=image,
        editable_scaffold=editable_scaffold_module_name,
    )

    editable_scaffold = _make_editable_scaffold(
        pipeline_name=pipeline_name,
        pipeline_description=pipeline_description,
        env_config=env_config,
        static_scaffold=static_scaffold_module_name,
        default_args=default_args,
    )

    with open(static_path, 'w') as fd:
        fd.write(static_scaffold)

    with open(editable_path, 'w') as fd:
        fd.write(editable_scaffold)

    return (static_path, editable_path)
