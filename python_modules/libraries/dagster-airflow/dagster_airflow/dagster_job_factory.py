from typing import AbstractSet, List, Mapping, Optional, Set, Tuple

from airflow.models.connection import Connection
from airflow.models.dagbag import DagBag
from dagster import (
    AssetKey,
    AssetsDefinition,
    Definitions,
    GraphDefinition,
    OutputMapping,
    TimeWindowPartitionsDefinition,
    _check as check,
)
from dagster._core.definitions.graph_definition import _create_adjacency_lists
from dagster._utils.schedules import is_valid_cron_schedule

from dagster_airflow.dagster_pipeline_factory import (
    DagsterAirflowError,
    _create_airflow_connections,
    _make_schedules_and_jobs_from_airflow_dag_bag,
    make_dagster_pipeline_from_airflow_dag,
    patch_airflow_example_dag,
)


def make_dagster_job_from_airflow_dag(
    dag,
    tags=None,
    use_airflow_template_context=False,
    unique_id=None,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
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
        use_airflow_template_context (bool): If True, will call get_template_context() on the
            Airflow TaskInstance model which requires and modifies the DagRun table. The use_airflow_template_context
            setting is ignored if use_ephemeral_airflow_db is True.
            (default: False)
        unique_id (int): If not None, this id will be postpended to generated op names. Used by
            framework authors to enforce unique op names within a repo.
        mock_xcom (bool): If True, dagster will mock out all calls made to xcom, features that
            depend on xcom may not work as expected. (default: False)
        use_ephemeral_airflow_db (bool): If True, dagster will create an ephemeral sqlite airflow
            database for each run. (default: False)
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB, if use_emphemeral_airflow_db is False this will be ignored.

    Returns:
        JobDefinition: The generated Dagster job

    """
    pipeline_def = make_dagster_pipeline_from_airflow_dag(
        dag=dag,
        tags=tags,
        use_airflow_template_context=use_airflow_template_context,
        unique_id=unique_id,
        mock_xcom=mock_xcom,
        use_ephemeral_airflow_db=use_ephemeral_airflow_db,
        connections=connections,
    )
    # pass in tags manually because pipeline_def.graph doesn't have it threaded
    return pipeline_def.graph.to_job(
        tags={**pipeline_def.tags},
        resource_defs={"airflow_db": pipeline_def.mode_definitions[0].resource_defs["airflow_db"]}
        if use_ephemeral_airflow_db
        else {},
    )


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
