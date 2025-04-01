import pytest
from airflow import __version__ as airflow_version
from airflow.models.dag import DAG
from airflow.operators.dummy_operator import DummyOperator  # type: ignore
from airflow.utils.dates import days_ago

if airflow_version >= "2.0.0":
    from airflow.models.baseoperator import chain
else:
    from airflow.utils.helpers import chain


from dagster._core.snap import JobSnap
from dagster._serdes import serialize_pp
from dagster_airflow.dagster_job_factory import make_dagster_job_from_airflow_dag

default_args = {
    "owner": "dagster",
    "start_date": days_ago(1),
}


@pytest.mark.requires_no_db
def test_one_task_dag(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="one_task_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="one_task_dag",
            default_args=default_args,
            schedule_interval=None,
        )
    _dummy_operator = DummyOperator(
        task_id="dummy_operator",
        dag=dag,
    )

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_two_task_dag_no_dep(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="two_task_dag_no_dep",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="two_task_dag_no_dep",
            default_args=default_args,
            schedule_interval=None,
        )
    _dummy_operator_1 = DummyOperator(
        task_id="dummy_operator_1",
        dag=dag,
    )
    _dummy_operator_2 = DummyOperator(
        task_id="dummy_operator_2",
        dag=dag,
    )

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_two_task_dag_with_dep(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="two_task_dag_with_dep",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="two_task_dag_with_dep",
            default_args=default_args,
            schedule_interval=None,
        )

    dummy_operator_1 = DummyOperator(
        task_id="dummy_operator_1",
        dag=dag,
    )
    dummy_operator_2 = DummyOperator(
        task_id="dummy_operator_2",
        dag=dag,
    )
    dummy_operator_1 >> dummy_operator_2  # pyright: ignore[reportUnusedExpression]

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_diamond_task_dag(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="diamond_task_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="diamond_task_dag",
            default_args=default_args,
            schedule_interval=None,
        )
    dummy_operator_1 = DummyOperator(
        task_id="dummy_operator_1",
        dag=dag,
    )
    dummy_operator_2 = DummyOperator(
        task_id="dummy_operator_2",
        dag=dag,
    )
    dummy_operator_3 = DummyOperator(
        task_id="dummy_operator_3",
        dag=dag,
    )
    dummy_operator_4 = DummyOperator(
        task_id="dummy_operator_4",
        dag=dag,
    )
    dummy_operator_1 >> dummy_operator_2  # pyright: ignore[reportUnusedExpression]
    dummy_operator_1 >> dummy_operator_3  # pyright: ignore[reportUnusedExpression]
    dummy_operator_2 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]
    dummy_operator_3 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_multi_root_dag(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="multi_root_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="multi_root_dag",
            default_args=default_args,
            schedule_interval=None,
        )
    dummy_operator_1 = DummyOperator(
        task_id="dummy_operator_1",
        dag=dag,
    )
    dummy_operator_2 = DummyOperator(
        task_id="dummy_operator_2",
        dag=dag,
    )
    dummy_operator_3 = DummyOperator(
        task_id="dummy_operator_3",
        dag=dag,
    )
    dummy_operator_4 = DummyOperator(
        task_id="dummy_operator_4",
        dag=dag,
    )
    dummy_operator_1 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]
    dummy_operator_2 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]
    dummy_operator_3 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]
    dag.tree_view()

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_multi_leaf_dag(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="multi_leaf_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="multi_leaf_dag",
            default_args=default_args,
            schedule_interval=None,
        )
    dummy_operator_1 = DummyOperator(
        task_id="dummy_operator_1",
        dag=dag,
    )
    dummy_operator_2 = DummyOperator(
        task_id="dummy_operator_2",
        dag=dag,
    )
    dummy_operator_3 = DummyOperator(
        task_id="dummy_operator_3",
        dag=dag,
    )
    dummy_operator_4 = DummyOperator(
        task_id="dummy_operator_4",
        dag=dag,
    )
    dummy_operator_1 >> dummy_operator_2  # pyright: ignore[reportUnusedExpression]
    dummy_operator_1 >> dummy_operator_3  # pyright: ignore[reportUnusedExpression]
    dummy_operator_1 >> dummy_operator_4  # pyright: ignore[reportUnusedExpression]

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_complex_dag(snapshot):
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="complex_dag",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="complex_dag",
            default_args=default_args,
            schedule_interval=None,
        )

    # Create
    create_entry_group = DummyOperator(
        task_id="create_entry_group",
        dag=dag,
    )
    create_entry_group_result = DummyOperator(
        task_id="create_entry_group_result",
        dag=dag,
    )
    create_entry_group_result2 = DummyOperator(
        task_id="create_entry_group_result2",
        dag=dag,
    )
    create_entry_gcs = DummyOperator(
        task_id="create_entry_gcs",
        dag=dag,
    )
    create_entry_gcs_result = DummyOperator(
        task_id="create_entry_gcs_result",
        dag=dag,
    )
    create_entry_gcs_result2 = DummyOperator(
        task_id="create_entry_gcs_result2",
        dag=dag,
    )
    create_tag = DummyOperator(
        task_id="create_tag",
        dag=dag,
    )
    create_tag_result = DummyOperator(
        task_id="create_tag_result",
        dag=dag,
    )
    create_tag_result2 = DummyOperator(
        task_id="create_tag_result2",
        dag=dag,
    )
    create_tag_template = DummyOperator(
        task_id="create_tag_template",
        dag=dag,
    )
    create_tag_template_result = DummyOperator(
        task_id="create_tag_template_result",
        dag=dag,
    )
    create_tag_template_result2 = DummyOperator(
        task_id="create_tag_template_result2",
        dag=dag,
    )
    create_tag_template_field = DummyOperator(
        task_id="create_tag_template_field",
        dag=dag,
    )
    create_tag_template_field_result = DummyOperator(
        task_id="create_tag_template_field_result",
        dag=dag,
    )

    # Delete
    delete_entry = DummyOperator(
        task_id="delete_entry",
        dag=dag,
    )
    create_entry_gcs >> delete_entry  # pyright: ignore[reportUnusedExpression]
    delete_entry_group = DummyOperator(
        task_id="delete_entry_group",
        dag=dag,
    )
    create_entry_group >> delete_entry_group  # pyright: ignore[reportUnusedExpression]
    delete_tag = DummyOperator(
        task_id="delete_tag",
        dag=dag,
    )
    create_tag >> delete_tag  # pyright: ignore[reportUnusedExpression]
    delete_tag_template_field = DummyOperator(
        task_id="delete_tag_template_field",
        dag=dag,
    )
    delete_tag_template = DummyOperator(
        task_id="delete_tag_template",
        dag=dag,
    )

    # Get
    get_entry_group = DummyOperator(
        task_id="get_entry_group",
        dag=dag,
    )
    get_entry_group_result = DummyOperator(
        task_id="get_entry_group_result",
        dag=dag,
    )
    get_entry = DummyOperator(
        task_id="get_entry",
        dag=dag,
    )
    get_entry_result = DummyOperator(
        task_id="get_entry_result",
        dag=dag,
    )
    get_tag_template = DummyOperator(
        task_id="get_tag_template",
        dag=dag,
    )
    get_tag_template_result = DummyOperator(
        task_id="get_tag_template_result",
        dag=dag,
    )

    # List
    list_tags = DummyOperator(
        task_id="list_tags",
        dag=dag,
    )
    list_tags_result = DummyOperator(
        task_id="list_tags_result",
        dag=dag,
    )

    # Lookup
    lookup_entry = DummyOperator(
        task_id="lookup_entry",
        dag=dag,
    )
    lookup_entry_result = DummyOperator(
        task_id="lookup_entry_result",
        dag=dag,
    )

    # Rename
    rename_tag_template_field = DummyOperator(
        task_id="rename_tag_template_field",
        dag=dag,
    )

    # Search
    search_catalog = DummyOperator(
        task_id="search_catalog",
        dag=dag,
    )
    search_catalog_result = DummyOperator(
        task_id="search_catalog_result",
        dag=dag,
    )

    # Update
    update_entry = DummyOperator(
        task_id="update_entry",
        dag=dag,
    )
    update_tag = DummyOperator(
        task_id="update_tag",
        dag=dag,
    )
    update_tag_template = DummyOperator(
        task_id="update_tag_template",
        dag=dag,
    )
    update_tag_template_field = DummyOperator(
        task_id="update_tag_template_field",
        dag=dag,
    )

    # Create
    create_tasks = [
        create_entry_group,
        create_entry_gcs,
        create_tag_template,
        create_tag_template_field,
        create_tag,
    ]
    chain(*create_tasks)

    create_entry_group >> delete_entry_group  # pyright: ignore[reportUnusedExpression]
    create_entry_group >> create_entry_group_result  # pyright: ignore[reportUnusedExpression]
    create_entry_group >> create_entry_group_result2  # pyright: ignore[reportUnusedExpression]

    create_entry_gcs >> delete_entry  # pyright: ignore[reportUnusedExpression]
    create_entry_gcs >> create_entry_gcs_result  # pyright: ignore[reportUnusedExpression]
    create_entry_gcs >> create_entry_gcs_result2  # pyright: ignore[reportUnusedExpression]

    create_tag_template >> delete_tag_template_field  # pyright: ignore[reportUnusedExpression]
    create_tag_template >> create_tag_template_result  # pyright: ignore[reportUnusedExpression]
    create_tag_template >> create_tag_template_result2  # pyright: ignore[reportUnusedExpression]

    create_tag_template_field >> delete_tag_template_field  # pyright: ignore[reportUnusedExpression]
    create_tag_template_field >> create_tag_template_field_result  # pyright: ignore[reportUnusedExpression]

    create_tag >> delete_tag  # pyright: ignore[reportUnusedExpression]
    create_tag >> create_tag_result  # pyright: ignore[reportUnusedExpression]
    create_tag >> create_tag_result2  # pyright: ignore[reportUnusedExpression]

    # Delete
    delete_tasks = [
        delete_tag,
        delete_tag_template_field,
        delete_tag_template,
        delete_entry_group,
        delete_entry,
    ]
    chain(*delete_tasks)

    # Get
    create_tag_template >> get_tag_template >> delete_tag_template  # pyright: ignore[reportUnusedExpression]
    get_tag_template >> get_tag_template_result  # pyright: ignore[reportUnusedExpression]

    create_entry_gcs >> get_entry >> delete_entry  # pyright: ignore[reportUnusedExpression]
    get_entry >> get_entry_result  # pyright: ignore[reportUnusedExpression]

    create_entry_group >> get_entry_group >> delete_entry_group  # pyright: ignore[reportUnusedExpression]
    get_entry_group >> get_entry_group_result  # pyright: ignore[reportUnusedExpression]

    # List
    create_tag >> list_tags >> delete_tag  # pyright: ignore[reportUnusedExpression]
    list_tags >> list_tags_result  # pyright: ignore[reportUnusedExpression]

    # Lookup
    create_entry_gcs >> lookup_entry >> delete_entry  # pyright: ignore[reportUnusedExpression]
    lookup_entry >> lookup_entry_result  # pyright: ignore[reportUnusedExpression]

    # Rename
    create_tag_template_field >> rename_tag_template_field >> delete_tag_template_field  # pyright: ignore[reportUnusedExpression]

    # Search
    chain(create_tasks, search_catalog, delete_tasks)
    search_catalog >> search_catalog_result  # pyright: ignore[reportUnusedExpression]

    # Update
    create_entry_gcs >> update_entry >> delete_entry  # pyright: ignore[reportUnusedExpression]
    create_tag >> update_tag >> delete_tag  # pyright: ignore[reportUnusedExpression]
    create_tag_template >> update_tag_template >> delete_tag_template  # pyright: ignore[reportUnusedExpression]
    create_tag_template_field >> update_tag_template_field >> rename_tag_template_field  # pyright: ignore[reportUnusedExpression]

    snapshot.assert_match(
        serialize_pp(
            JobSnap.from_job_def(make_dagster_job_from_airflow_dag(dag=dag)).dep_structure_snapshot
        )
    )


@pytest.mark.requires_no_db
def test_one_task_dag_to_job():
    if airflow_version >= "2.0.0":
        dag = DAG(
            dag_id="dag-with.dot-dash",
            default_args=default_args,
            schedule=None,
        )
    else:
        dag = DAG(
            dag_id="dag-with.dot-dash",
            default_args=default_args,
            schedule_interval=None,
        )
    _dummy_operator = DummyOperator(
        task_id="dummy_operator",
        dag=dag,
    )
    job_def = make_dagster_job_from_airflow_dag(dag=dag)

    assert job_def.name == "dag_with_dot_dash"
    assert len([job_def.nodes]) == 1
    result = job_def.execute_in_process()

    assert result.success
    step_success_events = [evt for evt in result.all_node_events if evt.is_step_success]
    assert len(step_success_events) == 1
    assert step_success_events[0].step_key == "dag_with_dot_dash__dummy_operator"
