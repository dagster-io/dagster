import importlib
import os
import tempfile
from typing import AbstractSet, List, Mapping, Optional, Set, Tuple

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
    AssetKey,
    AssetsDefinition,
    DagsterInvariantViolationError,
    Definitions,
    Field,
    GraphDefinition,
    JobDefinition,
    OutputMapping,
    TimeWindowPartitionsDefinition,
    _check as check,
    resource,
)
from dagster._core.definitions.graph_definition import _create_adjacency_lists
from dagster._core.definitions.utils import validate_tags
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR, IS_AIRFLOW_INGEST_PIPELINE_STR
from dagster._utils.schedules import is_valid_cron_schedule

from dagster_airflow.airflow_dag_converter import get_graph_definition_args
from dagster_airflow.dagster_pipeline_factory import (
    DagsterAirflowError,
    _create_airflow_connections,
    _make_schedules_and_jobs_from_airflow_dag_bag,
)
from dagster_airflow.patch_airflow_example_dag import patch_airflow_example_dag
from dagster_airflow.utils import Locker, normalized_name, serialize_connections

# pylint: disable=no-name-in-module,import-error
if str(airflow_version) >= "2.0.0":
    from airflow.utils.state import DagRunState
    from airflow.utils.types import DagRunType
else:
    from airflow.utils.state import State
# pylint: enable=no-name-in-module,import-error


def make_dagster_job_from_airflow_dag(
    dag,
    tags=None,
    unique_id=None,
    connections=None,
):
    """Construct a Dagster job corresponding to a given Airflow DAG.

    Tasks in the resulting job will execute the ``execute()`` method on the corresponding
    Airflow Operator. Dagster, any dependencies required by Airflow Operators, and the module
    containing your DAG definition must be available in the Python environment within which your
    Dagster solids execute.

    To set Airflow's ``execution_date`` for use with Airflow Operator's ``execute()`` methods,
    either:

    1. (Best for ad hoc runs) Execute job directly. This will set execution_date to the
        time (in UTC) of the run.

    2. Add ``{'airflow_execution_date': utc_date_string}`` to the job tags. This will override
        behavior from (1).

        .. code-block:: python

            my_dagster_job = make_dagster_job_from_airflow_dag(
                    dag=dag,
                    tags={'airflow_execution_date': utc_execution_date_str}
            )
            my_dagster_job.execute_in_process()

    3. (Recommended) Add ``{'airflow_execution_date': utc_date_string}`` to the run tags,
        such as in the Dagit UI. This will override behavior from (1) and (2)


    We apply normalized_name() to the dag id and task ids when generating job name and op
    names to ensure that names conform to Dagster's naming conventions.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster job
        tags (Dict[str, Field]): Job tags. Optionally include
            `tags={'airflow_execution_date': utc_date_string}` to specify execution_date used within
            execution of Airflow Operators.
        unique_id (int): If not None, this id will be postpended to generated op names. Used by
            framework authors to enforce unique op names within a repo.
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        JobDefinition: The generated Dagster job

    """
    check.inst_param(dag, "dag", DAG)
    tags = check.opt_dict_param(tags, "tags")
    unique_id = check.opt_int_param(unique_id, "unique_id")
    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    connections = check.opt_list_param(connections, "connections", of_type=Connection)

    if IS_AIRFLOW_INGEST_PIPELINE_STR not in tags:
        tags[IS_AIRFLOW_INGEST_PIPELINE_STR] = "true"

    tags = validate_tags(tags)

    node_dependencies, node_defs = get_graph_definition_args(dag=dag, unique_id=unique_id)

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
                _create_airflow_connections(
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

    graph_def = GraphDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        node_defs=node_defs,
        dependencies=node_dependencies,
        tags=tags,
    )

    job_def = JobDefinition(
        name=normalized_name(dag.dag_id),
        description="",
        resource_defs={"airflow_db": airflow_db},
        graph_def=graph_def,
        tags=tags,
        metadata={},
        op_retry_policy=None,
        version_strategy=None,
    )
    return job_def


def make_dagster_definitions_from_airflow_dag_bag(
    dag_bag,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct a Dagster definition corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_definition.py`:
            from dagster_airflow import make_dagster_definition_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_definition_from_dag_bag():
                return make_dagster_definition_from_airflow_dag_bag(my_dag_bag)

        Use Definitions as usual, for example:
            `dagit -f path/to/make_dagster_definition.py`

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
        Definitions
    """
    schedules, jobs = _make_schedules_and_jobs_from_airflow_dag_bag(
        dag_bag,
        use_airflow_template_context,
        mock_xcom,
        use_ephemeral_airflow_db,
        connections,
    )

    return Definitions(
        schedules=schedules,
        jobs=jobs,
    )


def make_dagster_definitions_from_airflow_dags_path(
    dag_path,
    safe_mode=True,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct a Dagster repository corresponding to Airflow DAGs in dag_path.

    Usage:
        Create ``make_dagster_definitions.py``:

        .. code-block:: python

            from dagster_airflow import make_dagster_definitions_from_airflow_dags_path

            def make_definitions_from_dir():
                return make_dagster_definitions_from_airflow_dags_path(
                    '/path/to/dags/',
                )

        Use RepositoryDefinition as usual, for example:
        ``dagit -f path/to/make_dagster_repo.py -n make_repo_from_dir``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
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
        Definitions
    """
    check.str_param(dag_path, "dag_path")
    check.bool_param(safe_mode, "safe_mode")
    check.bool_param(use_airflow_template_context, "use_airflow_template_context")
    mock_xcom = check.opt_bool_param(mock_xcom, "mock_xcom")
    use_ephemeral_airflow_db = check.opt_bool_param(
        use_ephemeral_airflow_db, "use_ephemeral_airflow_db"
    )
    connections = check.opt_list_param(connections, "connections", of_type=Connection)
    # add connections to airflow so that dag evaluation works
    _create_airflow_connections(connections)
    try:
        dag_bag = DagBag(
            dag_folder=dag_path,
            include_examples=False,  # Exclude Airflow example dags
            safe_mode=safe_mode,
        )
    except Exception:
        raise DagsterAirflowError("Error initializing airflow.models.dagbag object with arguments")

    return make_dagster_definitions_from_airflow_dag_bag(
        dag_bag=dag_bag,
        use_airflow_template_context=use_airflow_template_context,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        connections=connections,
    )


def make_dagster_definitions_from_airflow_example_dags(use_ephemeral_airflow_db=True):
    """Construct a Dagster repository for Airflow's example DAGs.

    Usage:

        Create `make_dagster_definitions.py`:
            from dagster_airflow import make_dagster_definitions_from_airflow_example_dags

            def make_airflow_example_dags():
                return make_dagster_definitions_from_airflow_example_dags()

        Use Definitions as usual, for example:
            `dagit -f path/to/make_dagster_definitions.py`

    Args:
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: True)

    Returns:
        Definitions
    """
    dag_bag = DagBag(
        dag_folder="some/empty/folder/with/no/dags",  # prevent defaulting to settings.DAGS_FOLDER
        include_examples=True,
    )

    # There is a bug in Airflow v1 where the python_callable for task
    # 'search_catalog' is missing a required position argument '_'. It is fixed in airflow v2
    patch_airflow_example_dag(dag_bag)

    return make_dagster_definitions_from_airflow_dag_bag(
        dag_bag=dag_bag, use_ephemeral_airflow_db=use_ephemeral_airflow_db
    )


def _build_asset_dependencies(
    graph: GraphDefinition,
    task_ids_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
    upstream_dependencies_by_asset_key: Mapping[AssetKey, AbstractSet[AssetKey]],
) -> Tuple[AbstractSet[OutputMapping], Mapping[str, AssetKey], Mapping[str, Set[AssetKey]]]:
    """Builds the asset dependency graph for a given set of airflow task mappings and a dagster graph
    """
    output_mappings = set()
    keys_by_output_name = {}
    internal_asset_deps: dict[str, Set[AssetKey]] = {}

    visited_nodes: dict[str, bool] = {}
    upstream_deps = set()

    def find_upstream_dependency(node_name: str) -> None:
        """find_upstream_dependency uses Depth-Firs-Search to find all upstream asset dependencies
        as described in task_ids_by_asset_key
        """
        # node has been visited
        if visited_nodes[node_name]:
            return
        # mark node as visted
        visited_nodes[node_name] = True
        # traverse upstream nodes
        for output_handle in graph.dependency_structure.all_upstream_outputs_from_node(node_name):
            forward_node = output_handle.node_name
            match = False
            # find any assets produced by upstream nodes and add them to the internal asset deps
            for asset_key in task_ids_by_asset_key:
                if forward_node.replace("airflow_", "") in task_ids_by_asset_key[asset_key]:
                    upstream_deps.add(asset_key)
                    match = True
            # don't traverse past nodes that have assets
            if not match:
                find_upstream_dependency(forward_node)

    # iterate through each asset to find all upstream asset dependencies
    for asset_key in task_ids_by_asset_key:
        asset_upstream_deps = set()
        for task_id in task_ids_by_asset_key[asset_key]:
            visited_nodes = {s.name: False for s in graph.nodes}
            upstream_deps = set()
            find_upstream_dependency(f"airflow_{task_id}")
            for dep in upstream_deps:
                asset_upstream_deps.add(dep)
            keys_by_output_name[f"result_airflow_{task_id}"] = asset_key
            output_mappings.add(
                OutputMapping(
                    graph_output_name=f"result_airflow_{task_id}",
                    mapped_node_name=f"airflow_{task_id}",
                    mapped_node_output_name="airflow_task_complete",  # Default output name
                )
            )

        # the tasks for a given asset should have the same internal deps
        for task_id in task_ids_by_asset_key[asset_key]:
            if f"result_airflow_{task_id}" in internal_asset_deps:
                internal_asset_deps[f"result_airflow_{task_id}"].update(asset_upstream_deps)
            else:
                internal_asset_deps[f"result_airflow_{task_id}"] = asset_upstream_deps
            # internal_asset_deps[f"result_airflow_{task_id}"] = asset_upstream_deps

    # add new upstream asset dependencies to the internal deps
    for asset_key in upstream_dependencies_by_asset_key:
        for key in keys_by_output_name:
            if keys_by_output_name[key] == asset_key:
                internal_asset_deps[key].update(upstream_dependencies_by_asset_key[asset_key])

    return (output_mappings, keys_by_output_name, internal_asset_deps)


def load_assets_from_airflow_dag(
    dag,
    task_ids_by_asset_key: Mapping[AssetKey, AbstractSet[str]] = {},
    upstream_dependencies_by_asset_key: Mapping[AssetKey, AbstractSet[AssetKey]] = {},
    connections: Optional[List[Connection]] = None,
) -> List[AssetsDefinition]:
    """[Experimental] Construct Dagster Assets for a given Airflow DAG.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster job
        task_ids_by_asset_key (Optional[Mapping[AssetKey, AbstractSet[str]]]): A mapping from asset
            keys to task ids. Used break up the Airflow Dag into multiple SDAs
        upstream_dependencies_by_asset_key (Optional[Mapping[AssetKey, AbstractSet[AssetKey]]]): A
            mapping from upstream asset keys to assets provided in task_ids_by_asset_key. Used to
            declare new upstream SDA depenencies.
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB

    Returns:
        List[AssetsDefinition]
    """
    cron_schedule = dag.normalized_schedule_interval
    if cron_schedule is not None and not is_valid_cron_schedule(cron_schedule):
        raise DagsterAirflowError(
            "Invalid cron schedule: {} in DAG {}".format(cron_schedule, dag.dag_id)
        )

    job = make_dagster_job_from_airflow_dag(
        dag, use_ephemeral_airflow_db=True, connections=connections
    )
    graph = job._graph_def
    start_date = dag.start_date if dag.start_date else dag.default_args.get("start_date")

    # leaf nodes have no downstream nodes
    forward_edges, _ = _create_adjacency_lists(graph.nodes, graph.dependency_structure)
    leaf_nodes = {
        node_name.replace("airflow_", "")
        for node_name, downstream_nodes in forward_edges.items()
        if not downstream_nodes
    }

    mutated_task_ids_by_asset_key: dict[AssetKey, set[str]] = {}

    if task_ids_by_asset_key is None or task_ids_by_asset_key == {}:
        # if no mappings are provided the dag becomes a single SDA
        task_ids_by_asset_key = {AssetKey(dag.dag_id): leaf_nodes}
    else:
        # if mappings were provide any unmapped leaf nodes are added to a default asset
        used_nodes: set[str] = set()
        for key in task_ids_by_asset_key:
            used_nodes.update(task_ids_by_asset_key[key])

        mutated_task_ids_by_asset_key[AssetKey(dag.dag_id)] = leaf_nodes - used_nodes

    for key in task_ids_by_asset_key:
        if key not in mutated_task_ids_by_asset_key:
            mutated_task_ids_by_asset_key[key] = set(task_ids_by_asset_key[key])
        else:
            mutated_task_ids_by_asset_key[key].update(task_ids_by_asset_key[key])

    output_mappings, keys_by_output_name, internal_asset_deps = _build_asset_dependencies(
        graph, mutated_task_ids_by_asset_key, upstream_dependencies_by_asset_key
    )

    new_graph = GraphDefinition(
        name=graph.name,
        node_defs=graph.node_defs,
        dependencies=graph.dependencies,
        output_mappings=list(output_mappings),
    )

    asset_def = AssetsDefinition.from_graph(
        graph_def=new_graph,
        partitions_def=TimeWindowPartitionsDefinition(
            cron_schedule=cron_schedule,
            timezone=dag.timezone.name,
            start=start_date.strftime("%Y-%m-%dT%H:%M:%S"),
            fmt="%Y-%m-%dT%H:%M:%S",
        )
        if cron_schedule is not None
        else None,
        resource_defs=job.resource_defs,
        group_name=dag.dag_id,
        keys_by_output_name=keys_by_output_name,
        internal_asset_deps=internal_asset_deps,
        can_subset=True,
    )
    return [asset_def]
