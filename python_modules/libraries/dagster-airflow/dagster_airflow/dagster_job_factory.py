from dagster_airflow.dagster_pipeline_factory import (
    make_dagster_pipeline_from_airflow_dag,
    make_dagster_repo_from_airflow_dag_bag,
    make_dagster_repo_from_airflow_dags_path,
)

from dagster import Definitions


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
    refresh_from_airflow_db=False,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=False,
    connections=None,
):
    """Construct Dagster definitions corresponding to Airflow DAGs in DagBag.

    Usage:
        Create `make_dagster_definition.py`:
            from dagster_airflow import make_dagster_definition_from_airflow_dag_bag
            from airflow_home import my_dag_bag

            def make_definition_from_dag_bag():
                return make_dagster_definition_from_airflow_dag_bag(my_dag_bag)

            `dagit -f path/to/make_dagster_definition.py`

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        refresh_from_airflow_db (bool): If True, will refresh DAG if expired via DagBag.get_dag(),
            which requires access to initialized Airflow DB. If False (recommended), gets dag from
            DagBag's dags dict without depending on Airflow DB. (default: False)
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

    repo = make_dagster_repo_from_airflow_dag_bag(
        dag_bag,
        "dagster_airflow_repo",
        refresh_from_airflow_db,
        use_airflow_template_context,
        mock_xcom,
        use_ephemeral_airflow_db,
        connections,
    )

    return Definitions(
        schedules=repo.schedule_defs,
        jobs=repo.get_all_jobs(),
    )


def make_dagster_definitions_from_airflow_dags_path(
    dag_path,
    safe_mode=True,
    store_serialized_dags=False,
    use_airflow_template_context=False,
    mock_xcom=False,
    use_ephemeral_airflow_db=True,
    connections=None,
):
    """Construct Dagster definitions corresponding to Airflow DAGs in dag_path.

    ``DagBag.get_dag()`` dependency requires Airflow DB to be initialized.

    Usage:
        Create ``make_dagster_definitions.py``:

        .. code-block:: python

            from dagster_airflow.dagster_pipeline_factory import make_dagster_definitions_from_airflow_dags_path

            def make_definitions_from_dir():
                return make_dagster_definitions_from_airflow_dags_path(
                    '/path/to/dags/'
                )

        ``dagit -f path/to/make_dagster_definitions.py``

    Args:
        dag_path (str): Path to directory or file that contains Airflow Dags
        safe_mode (bool): True to use Airflow's default heuristic to find files that contain DAGs
            (ie find files that contain both b'DAG' and b'airflow') (default: True)
        store_serialized_dags (bool): True to read Airflow DAGS from Airflow DB. False to read DAGS
            from Python files. (default: False)
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

    repo = make_dagster_repo_from_airflow_dags_path(
        dag_path,
        "dagster_airflow_repo",
        safe_mode,
        store_serialized_dags,
        use_airflow_template_context,
        mock_xcom,
        use_ephemeral_airflow_db,
        connections,
    )

    return Definitions(
        schedules=repo.schedule_defs,
        jobs=repo.get_all_jobs(),
    )
