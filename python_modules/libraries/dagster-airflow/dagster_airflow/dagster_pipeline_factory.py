import importlib
import os
import tempfile

import airflow
import dateutil
import pytz
from airflow import __version__ as airflow_version
from airflow.models.connection import Connection
from airflow.models.dag import DAG
from airflow.models.dagbag import DagBag
from airflow.utils import db
from dagster import (
    Array,
    DagsterInvariantViolationError,
    Field,
    _check as check,
    repository,
    resource,
)
from dagster._core.definitions.utils import validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dagster._legacy import ModeDefinition, PipelineDefinition

from dagster_airflow.airflow_dag_converter import get_pipeline_definition_args
from dagster_airflow.dagster_schedule_factory import make_dagster_schedule_from_airflow_dag
from dagster_airflow.patch_airflow_example_dag import patch_airflow_example_dag
from dagster_airflow.utils import (
    DagsterAirflowError,
    Locker,
    contains_duplicate_task_names,
    create_airflow_connections,
    normalized_name,
    serialize_connections,
)

# pylint: disable=no-name-in-module,import-error
if str(airflow_version) >= "2.0.0":
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State
# pylint: enable=no-name-in-module,import-error


def _make_schedules_and_jobs_from_airflow_dag_bag(
    dag_bag,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct Dagster Schedules and Jobs corresponding to Airflow DagBag.

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        - List[ScheduleDefinition]: The generated Dagster Schedules
        - List[JobDefinition]: The generated Dagster Jobs
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    use_unique_id = contains_duplicate_task_names(dag_bag)

    job_defs = []
    schedule_defs = []
    count = 0
    # To enforce predictable iteration order
    sorted_dag_ids = sorted(dag_bag.dag_ids)
    for dag_id in sorted_dag_ids:
        dag = dag_bag.dags.get(dag_id)
        if not use_unique_id:
            pipeline_def = make_dagster_pipeline_from_airflow_dag(
                dag=dag,
                tags=None,
                use_airflow_template_context=use_airflow_template_context,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
                connections=connections,
            )
        else:
            pipeline_def = make_dagster_pipeline_from_airflow_dag(
                dag=dag,
                tags=None,
                use_airflow_template_context=use_airflow_template_context,
                unique_id=count,
                mock_xcom=mock_xcom,
                use_ephemeral_airflow_db=use_ephemeral_airflow_db,
                connections=connections,
            )
            count += 1
        # pass in tags manually because pipeline_def.graph doesn't have it threaded
        job_def = pipeline_def.graph.to_job(
            tags={**pipeline_def.tags},
            resource_defs={
                "airflow_db": pipeline_def.mode_definitions[0].resource_defs["airflow_db"]
            }
            if use_ephemeral_airflow_db
            else {},
        )
        schedule_def = make_dagster_schedule_from_airflow_dag(
            dag=dag,
            job_def=job_def,
        )
        if schedule_def:
            schedule_defs.append(schedule_def)
        else:
            job_defs.append(job_def)

    return schedule_defs, job_defs


def make_dagster_repo_from_airflow_dag_bag(
    dag_bag,
    repo_name,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_repo_from_dag_bag():
                return make_dagster_repo_from_airflow_dag_bag(my_dag_bag, 'my_repo_name')

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_repo_from_dag_bag`

    Args:
        dag_bag (DagBag): Airflow DagBag Model
        repo_name (str): Name for generated RepositoryDefinition
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        RepositoryDefinition
    """
    check.inst_param(dag_bag, "dag_bag", DagBag)
    check.str_param(repo_name, "repo_name")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    schedules, jobs = _make_schedules_and_jobs_from_airflow_dag_bag(
        dag_bag,
        use_airflow_template_context,
        mock_xcom,
        use_ephemeral_airflow_db,
        connections,
    )

    @repository(name=repo_name)
    def _repo():
        return [jobs, schedules]

    return _repo


def make_dagster_repo_from_airflow_example_dags(
    repo_name="airflow_example_dags_repo", use_ephemeral_airflow_db=True
):
    """Construct a Dagster repository for Airflow's example DAGs.

    Usage:

        Create `make_dagster_repo.py`:
            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_example_dags

            def make_airflow_example_dags():
                return make_dagster_repo_from_airflow_example_dags()

        Use RepositoryDefinition as usual, for example:
            `dagit -f path/to/make_dagster_repo.py -n make_airflow_example_dags`

    Args:
        repo_name (str): Name for generated RepositoryDefinition
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: True)

    Returns:
        RepositoryDefinition
    """
    dag_bag = DagBag(
        dag_folder="some/empty/folder/with/no/dags",  # prevent defaulting to settings.DAGS_FOLDER
        include_examples=True,
    )

    # There is a bug in Airflow v1 where the python_callable for task
    # 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2
    patch_airflow_example_dag(dag_bag)

    return make_dagster_repo_from_airflow_dag_bag(
        dag_bag=dag_bag, repo_name=repo_name, use_ephemeral_airflow_db=use_ephemeral_airflow_db
    )


def make_dagster_repo_from_airflow_dags_path(
    dag_path,
    repo_name,
    safe_mode=True,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    Usage:
        Create ``make_dagster_repo.py``:

        .. code-block:: python

            from dagster_airflow.dagster_pipeline_factory import make_dagster_repo_from_airflow_dags_path

            def make_repo_from_dir():
                return make_dagster_repo_from_airflow_dags_path(
                    '/path/to/dags/', 'my_repo_name'
                )

        Use RepositoryDefinition as usual, for example:
        ``dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        repo_name (str): Name for generated RepositoryDefinition
        include_examples (bool): True to include Airflow's example DAGs. (default: False)
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        RepositoryDefinition
    """
    check.str_param(dag_path, "dag_path")
    check.str_param(repo_name, "repo_name")
    check.bool_param(safe_mode, "safe_mode")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)
    # add connections to airflow so that dag evaluation works
    create_airflow_connections(connections)
    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example dags
            safe_mode=safe_mode,
        )
    except Exception:
        raise DagsterAirflowError("Error initializing airflow.models.dagbag object with arguments")

    return make_dagster_repo_from_airflow_dag_bag(
        dag_bag=dag_bag,
        repo_name=repo_name,
        use_airflow_template_context=use_airflow_template_context,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        connections=connections,
    )


def make_dagster_pipeline_from_airflow_dag(
    dag,
    tags=None,
    use_airflow_template_context=False,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct a Dagster pipeline corresponding to a given Airflow DAG.

    Tasks in the resulting pipeline will execute the ``execute()`` method on the corresponding
    Airflow Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which your
    Dagster solids execute.

    To set Airflow's ``execution_date`` for use with Airflow Operator's ``execute()`` methods,
    either:

    1. (Best for ad hoc runs) Run Pipeline with 'default' preset, which sets execution_date to the
        time (in UTC) of pipeline invocation:

        .. code-block:: python

            execute_pipeline(
                pipeline=make_dagster_pipeline_from_airflow_dag(dag=dag),
                preset='default')

    2. Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineDefinition tags. This will
       override behavior from (1).

        .. code-block:: python

            execute_pipeline(
                make_dagster_pipeline_from_airflow_dag(
                    dag=dag,
                    tags={'airflow_execution_date': utc_execution_date_str}
                )
            )

    3. (Recommended) Add ``{'airflow_execution_date': utc_date_string}`` to the PipelineRun tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)


    We apply normalized_name() to the dag id and task ids when generating pipeline name and solid
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster pipeline
        tags (Dict[str, Field]): Pipeline tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        unique_id (int): If not None, this id will be postpended to generated solid names. Used by
            framework authors to enforce unique solid names within a repo.
        mock_xcom (bool): If not None, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected.
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        pipeline_def (PipelineDefinition): The generated Dagster pipeline

    """
    check.inst_param(dag, "dag", DAG)
    tags = check.opt_dict_param(tags, "tags")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    tags = validate_tags(tags)

    pipeline_dependencies, solid_defs = get_pipeline_definition_args(
        dag=dag,
        use_airflow_template_context=use_airflow_template_context,
        unique_id=unique_id,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
    )

    serialized_connections = serialize_connections(connections)

    @resource(
        config_schema={
            "dag_location": Field(str, default_value=dag.fileloc),
            "dag_id": Field(str, default_value=dag.dag_id),
            "connections": Field(
                Array(inner_type=dict),
                default_value=serialized_connections,
                is_required=False,
            ),
        }
    )
    def airflow_db(context):
        airflow_home_path = os.path.join(tempfile.gettempdir(), f"dagster_airflow_{context.run_id}")
        os.environ["AIRFLOW_HOME"] = airflow_home_path
        os.makedirs(airflow_home_path, exist_ok=True)
        with Locker(airflow_home_path):
            airflow_initialized = os.path.exists(f"{airflow_home_path}/airflow.db")
            # because AIRFLOW_HOME has been overriden airflow needs to be reloaded
            if airflow_version >= "2.0.0":
                importlib.reload(airflow.configuration)
                importlib.reload(airflow.settings)
                importlib.reload(airflow)
            else:
                importlib.reload(airflow)
            if not airflow_initialized:
                db.initdb()
                create_airflow_connections(
                    [Connection(**c) for c in context.resource_config["connections"]]
                )

            dag_bag = airflow.models.dagbag.DagBag(
                dag_folder=context.resource_config["dag_location"], include_examples=False
            )
            dag = dag_bag.get_dag(context.resource_config["dag_id"])
            if AIRFLOW_EXECUTION_DATE_STR in context.dagster_run.tags:
                # for airflow DAGs that have not been turned into SDAs
                execution_date_str = context.dagster_run.tags.get(AIRFLOW_EXECUTION_DATE_STR)
                check.str_param(execution_date_str, "execution_date_str")
                try:
                    execution_date = dateutil.parser.parse(execution_date_str)
                except ValueError:
                    raise DagsterInvariantViolationError(
                        'Could not parse execution_date "{execution_date_str}". Please use datetime'
                        " format compatible with  dateutil.parser.parse.".format(
                            execution_date_str=execution_date_str,
                        )
                    )
                except OverflowError:
                    raise DagsterInvariantViolationError(
                        'Date "{execution_date_str}" exceeds the largest valid C integer on the'
                        " system.".format(
                            execution_date_str=execution_date_str,
                        )
                    )
            elif "dagster/partition" in context.dagster_run.tags:
                # for airflow DAGs that have been turned into SDAs
                execution_date_str = context.dagster_run.tags.get("dagster/partition")
                execution_date = dateutil.parser.parse(execution_date_str)
                execution_date = execution_date.replace(tzinfo=pytz.timezone(dag.timezone.name))
            else:
                raise DagsterInvariantViolationError(
                    'Could not find "{AIRFLOW_EXECUTION_DATE_STR}" in tags "{tags}". Please '
                    'add "{AIRFLOW_EXECUTION_DATE_STR}" to tags before executing'.format(
                        AIRFLOW_EXECUTION_DATE_STR=AIRFLOW_EXECUTION_DATE_STR,
                        tags=context.dagster_run.tags,
                    )
                )

            dagrun = dag.get_dagrun(execution_date=execution_date)
            if not dagrun:
                if airflow_version >= "2.0.0":
                    dagrun = dag.create_dagrun(
                        state=DagRunState.RUNNING,
                        execution_date=execution_date,
                        run_type=DagRunType.MANUAL,
                    )
                else:
                    dagrun = dag.create_dagrun(
                        run_id=f"dagster_airflow_run_{execution_date}",
                        state=State.RUNNING,
                        execution_date=execution_date,
                    )

        return {
            "dag": dag,
            "dagrun": dagrun,
        }

    pipeline_def = PipelineDefinition(
        name=normalized_name(dag.dag_id),
        solid_defs=solid_defs,
        dependencies=pipeline_dependencies,
        mode_defs=[ModeDefinition(resource_defs={"airflow_db": airflow_db})]
        if use_ephemeral_airflow_db
        else [],
        tags=tags,
    )
    return pipeline_def
