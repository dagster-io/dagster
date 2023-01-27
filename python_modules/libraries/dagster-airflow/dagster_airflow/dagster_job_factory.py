from datetime import datetime
from pprint import pprint

from airflow.models.connection import Connection
from airflow.models.dagbag import DagBag
from dagster_airflow.dagster_pipeline_factory import (
    DagsterAirflowError, _create_airflow_connections,
    _make_schedules_and_jobs_from_airflow_dag_bag,
    make_dagster_pipeline_from_airflow_dag, patch_airflow_example_dag)

from dagster import (AssetKey, AssetOut, AssetsDefinition, Definitions,
                     GraphDefinition, GraphOut, Output, OutputMapping,
                     TimeWindowPartitionsDefinition)
from dagster import _check as check
from dagster import multi_asset
from dagster._core.definitions.graph_definition import _create_adjacency_lists
from dagster._core.instance import AIRFLOW_EXECUTION_DATE_STR
from dagster._utils.schedules import is_valid_cron_schedule


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

def make_graph_backed_assets_from_airflow_dag(
    dag,
    asset_key_to_task_ids=None,
    connections=None,
):
    """Construct a Dagster Assets forr Airflow DAG.

    Args:
        dag (DAG): The Airflow DAG to compile into a Dagster job
        asset_key_to_task_ids (Optional[Dict[str, Union[str, set[str]]]]): A mapping from asset keys to task ids
        connections (List[Connection]): List of Airflow Connections to be created in the Ephemeral
            Airflow DB

    Returns:
        AssetDefinition
    """
    cron_schedule = dag.normalized_schedule_interval

    job = make_dagster_job_from_airflow_dag(dag, use_ephemeral_airflow_db=True, connections=connections)
    graph = job._graph_def
    start_date = dag.start_date if dag.start_date else dag.default_args.get("start_date")

    # if no asset_
    if asset_key_to_task_ids is None or asset_key_to_task_ids == {}:
        # leaf nodes have no downstream nodes
        forward_edges, _ = _create_adjacency_lists(graph.solids, graph.dependency_structure)
        leaf_nodes = {
            node_name.replace('airflow_', "") for node_name, downstream_nodes in forward_edges.items() if not downstream_nodes
        }
        asset_key_to_task_ids = {
            dag.dag_id: leaf_nodes
        }

    output_mappings=set()
    keys_by_output_name = {}
    internal_asset_deps={}

    visit_dict = {}
    upstream_deps = set()

    def find_upstream_dependency(solid_name: str) -> None:
        # DFS to find all upsteam dependencies
        # this node has been visited
        if visit_dict[solid_name]:
            return
        # mark node as visted
        visit_dict[solid_name] = True
        # traverse upstream nodes
        for output_handle in graph.dependency_structure.all_upstream_outputs_from_node(solid_name):
            forward_node = output_handle.node_name
            match = False
            # find any assets produced by upstream nodes and add them to the internal asset deps
            for asset_key in asset_key_to_task_ids:
                if forward_node.replace('airflow_', "") in asset_key_to_task_ids[asset_key]:
                    upstream_deps.add(AssetKey(asset_key))
                    match = True
            # don't traverse past nodes that have assets
            if not match:
                find_upstream_dependency(forward_node)

    for asset_key in asset_key_to_task_ids:
        asset_upstream_deps = set()
        for task_id in asset_key_to_task_ids[asset_key]:
            visit_dict = {s.name: False for s in graph.solids}
            upstream_deps = set()
            find_upstream_dependency(f"airflow_{task_id}")
            for dep in upstream_deps:
                asset_upstream_deps.add(dep)
            internal_asset_deps[f"result_airflow_{task_id}"] = upstream_deps
            keys_by_output_name[f"result_airflow_{task_id}"] = AssetKey(asset_key)
            output_mappings.add(OutputMapping(
                graph_output_name=f"result_airflow_{task_id}",
                mapped_node_name=f"airflow_{task_id}",
                mapped_node_output_name="airflow_task_complete" # Default output name
            ))

        # the tasks for a given asset should have the same internal deps
        for task_id in asset_key_to_task_ids[asset_key]:
            internal_asset_deps[f"result_airflow_{task_id}"] = asset_upstream_deps

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
            start=start_date.strftime("%Y-%m-%d"),
            fmt="%Y-%m-%d"
        ) if isinstance(cron_schedule, str) and is_valid_cron_schedule(cron_schedule) else None,
        resource_defs=job.resource_defs,
        group_name=dag.dag_id,
        keys_by_output_name=keys_by_output_name,
        internal_asset_deps=internal_asset_deps,
        can_subset=True
    )
    return asset_def