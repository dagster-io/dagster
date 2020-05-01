import datetime
import logging
import sys
from contextlib import contextmanager

import dateutil
from airflow.models import TaskInstance
from airflow.models.baseoperator import BaseOperator
from airflow.models.dag import DAG
from airflow.models.dagbag import DagBag
from airflow.settings import LOG_FORMAT

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    InputDefinition,
    MultiDependencyDefinition,
    Nothing,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidDefinition,
    check,
    solid,
)
from dagster.core.definitions.utils import VALID_NAME_REGEX, validate_tags
from dagster.core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR


class DagsterAirflowError(Exception):
    pass


def make_dagster_repo_from_airflow_dag_bag(dag_bag, repo_name):
    ''' Construct a Dagster repository corresponding to Airflow DAGs in DagBag.

    DagBag.get_dag() dependency requires Airflow DB to be initialized

    Usage:
        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_repo_from_dag_bag():
                return make_dagster_repo_from_airflow_dag_bag(my_dag_bag, 'my_repo_name')

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_repo_from_dag_bag`

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition

    Returns:
        RepositoryDefinition
    '''
    check.inst_param(dag_bag, 'dag_bag', DagBag)
    check.str_param(repo_name, 'repo_name')

    pipeline_defs = []
    for dag_id in dag_bag.dag_ids:
        pipeline_defs.append(make_dagster_pipeline_from_airflow_dag(dag_bag.get_dag(dag_id)))

    return RepositoryDefinition(name=repo_name, pipeline_defs=pipeline_defs)


def make_dagster_repo_from_airflow_dags_path(
    dag_path, repo_name, safe_mode=True, store_serialized_dags=False
):
    ''' Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    DagBag.get_dag() dependency requires Airflow DB to be initialized.

    Usage:

        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dags_path

            def make_repo_from_dir():
                return make_dagster_repo_from_airflow_dags_path(
                    '/path/to/dags/', 'my_repo_name'
                )
        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir`

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        store_serialized_dags (bool): True to read Airflow DAGS from Airflow DB. False to read DAGS
            from Python files. (default: False)

    Returns:
        RepositoryDefinition
    '''
    check.str_param(dag_path, 'dag_path')
    check.str_param(repo_name, 'repo_name')
    check.bool_param(safe_mode, 'safe_mode')
    check.bool_param(store_serialized_dags, 'store_serialized_dags')

    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example DAGs
            safe_mode=safe_mode,
            store_serialized_dags=store_serialized_dags,
        )
    except Exception:  # pylint: disable=broad-except
        raise DagsterAirflowError('Error initializing airflow.models.dagbag object with arguments')

    return make_dagster_repo_from_airflow_dag_bag(dag_bag, repo_name)


def make_dagster_pipeline_from_airflow_dag(dag, tags=None):
    '''Construct a Dagster pipeline corresponding to a given Airflow DAG.

    Tasks in the resulting pipeline will execute the execute() method on the corresponding Airflow
    Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which
    your Dagster solids execute.

    To set Airflow's `execution_date` for use with Airflow Operator's execute() methods, either
        (1) (Best for ad hoc runs) Run Pipeline with 'default' preset, which sets execution_date to
        the time (in UTC) of pipeline invocation

        ```
        execute_pipeline(
            pipeline=make_dagster_pipeline_from_airflow_dag(dag),
            preset='default')
        ```

        (2) Add {'airflow_execution_date': utc_date_string} to the PipelineDefinition tags. This
        will override behavior from (1).

        ```
        execute_pipeline(
            make_dagster_pipeline_from_airflow_dag(
                dag,
                {'airflow_execution_date': utc_execution_date_str}
            )
        )
        ```

        (3) (Recommended) Add {'airflow_execution_date': utc_date_string} to the PipelineRun tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)

    We apply normalized_name() to the dag id and task ids when generating pipeline name and solid
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster pipeline
        tags (Dict[str, Field]): Pipeline tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.

    Returns:
        pipeline_def (PipelineDefinition): The generated Dagster pipeline

    '''
    check.inst_param(dag, 'dag', DAG)
    tags = check.opt_dict_param(tags, 'tags')

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = 'true'

    tags = validate_tags(tags)

    pipeline_dependencies, solid_defs = _get_pipeline_definition_args(dag)
    pipeline_def = PipelineDefinition(
        name=normalized_name(dag.dag_id),
        solid_defs=solid_defs,
        dependencies=pipeline_dependencies,
        tags=tags,
    )
    return pipeline_def


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
def normalized_name(name):
    return 'airflow_' + ''.join(c if VALID_NAME_REGEX.match(c) else '_' for c in name)


def _get_pipeline_definition_args(dag):
    check.inst_param(dag, 'dag', DAG)
    pipeline_dependencies = {}
    solid_defs = []
    seen_tasks = []

    # To enforce predictable iteration order
    dag_roots = sorted(dag.roots, key=lambda x: x.task_id)
    for task in dag_roots:
        _traverse_airflow_dag(task, seen_tasks, pipeline_dependencies, solid_defs)
    return (pipeline_dependencies, solid_defs)


def _traverse_airflow_dag(task, seen_tasks, pipeline_dependencies, solid_defs):
    check.inst_param(task, 'task', BaseOperator)
    check.list_param(seen_tasks, 'seen_tasks', BaseOperator)
    check.list_param(solid_defs, 'solid_defs', SolidDefinition)

    seen_tasks.append(task)
    current_solid = make_dagster_solid_from_airflow_task(task)
    solid_defs.append(current_solid)

    if len(task.upstream_list) > 0:
        # To enforce predictable iteration order
        task_upstream_list = sorted(task.upstream_list, key=lambda x: x.task_id)

        pipeline_dependencies[current_solid.name] = {
            'airflow_task_ready': MultiDependencyDefinition(
                [
                    DependencyDefinition(
                        solid=normalized_name(task_upstream.task_id),
                        output='airflow_task_complete',
                    )
                    for task_upstream in task_upstream_list
                ]
            )
        }

    # To enforce predictable iteration order
    task_downstream_list = sorted(task.downstream_list, key=lambda x: x.task_id)
    for child_task in task_downstream_list:
        if child_task not in seen_tasks:
            _traverse_airflow_dag(child_task, seen_tasks, pipeline_dependencies, solid_defs)


@contextmanager
def replace_airflow_logger_handlers():
    try:
        # Redirect airflow handlers to stdout / compute logs
        prev_airflow_handlers = logging.getLogger('airflow.task').handlers
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root = logging.getLogger('airflow.task')
        root.handlers = [handler]
        yield
    finally:
        # Restore previous log handlers
        logging.getLogger('airflow.task').handlers = prev_airflow_handlers


def make_dagster_solid_from_airflow_task(task):
    check.inst_param(task, 'task', BaseOperator)

    @solid(
        name=normalized_name(task.task_id),
        input_defs=[InputDefinition('airflow_task_ready', Nothing)],
        output_defs=[OutputDefinition(Nothing, 'airflow_task_complete')],
    )
    def _solid(context):  # pylint: disable=unused-argument
        if AIRFLOW_EXECUTION_DATE_STR not in context.pipeline_run.tags:
            raise DagsterInvariantViolationError(
                'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in pipeline tags "{tags}". Please '
                'add "{AIRFLOW_EXECUTION_DATE_STR}" to pipeline tags before executing'.format(
                    AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                    tags=context.pipeline_run.tags,
                )
            )
        execution_date_str = context.pipeline_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)

        check.str_param(execution_date_str, 'execution_date_str')
        try:
            execution_date = dateutil.parser.parse(execution_date_str)
        except ValueError:
            raise DagsterInvariantViolationError(
                'Could not parse execution_date "{execution_date_str}". Please use datetime format '
                'compatible with  dateutil.parser.parse.'.format(
                    execution_date_str=execution_date_str,
                )
            )
        except OverflowError:
            raise DagsterInvariantViolationError(
                'Date "{execution_date_str}" exceeds the largest valid C integer on the system.'.format(
                    execution_date_str=execution_date_str,
                )
            )

        check.inst_param(execution_date, 'execution_date', datetime.datetime)

        with replace_airflow_logger_handlers():
            task_instance = TaskInstance(task=task, execution_date=execution_date)

            ti_context = task_instance.get_template_context()
            task.render_template_fields(ti_context)

            task.execute(ti_context)
            return None

    return _solid
