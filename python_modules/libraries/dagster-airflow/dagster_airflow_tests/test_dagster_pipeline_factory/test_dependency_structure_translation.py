# pylint: disable=pointless-statement

from airflow.models.dag import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.helpers import chain
from dagster.core.snap import PipelineSnapshot
from dagster.serdes import serialize_pp
from dagster_airflow.dagster_pipeline_factory import make_dagster_pipeline_from_airflow_dag

default_args = {
    "owner": "dagster",
    "start_date": days_ago(1),
}


def test_one_task_dag(snapshot):
    dag = DAG(
        dag_id="one_task_dag",
        default_args=default_args,
        schedule_interval=None,
    )
    dummy_operator = DummyOperator(
        task_id="dummy_operator",
        dag=dag,
    )

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_two_task_dag_no_dep(snapshot):
    dag = DAG(
        dag_id="two_task_dag_no_dep",
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

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_two_task_dag_with_dep(snapshot):
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
    dummy_operator_1 >> dummy_operator_2

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_diamond_task_dag(snapshot):
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
    dummy_operator_1 >> dummy_operator_2
    dummy_operator_1 >> dummy_operator_3
    dummy_operator_2 >> dummy_operator_4
    dummy_operator_3 >> dummy_operator_4

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_multi_root_dag(snapshot):
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
    dummy_operator_1 >> dummy_operator_4
    dummy_operator_2 >> dummy_operator_4
    dummy_operator_3 >> dummy_operator_4
    dag.tree_view()

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_multi_leaf_dag(snapshot):
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
    dummy_operator_1 >> dummy_operator_2
    dummy_operator_1 >> dummy_operator_3
    dummy_operator_1 >> dummy_operator_4

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )


def test_complex_dag(snapshot):
    dag = DAG(dag_id="complex_dag", default_args=default_args, schedule_interval=None)

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
    create_tag_template_field_result2 = DummyOperator(
        task_id="create_tag_template_field_result",
        dag=dag,
    )

    # Delete
    delete_entry = DummyOperator(
        task_id="delete_entry",
        dag=dag,
    )
    create_entry_gcs >> delete_entry
    delete_entry_group = DummyOperator(
        task_id="delete_entry_group",
        dag=dag,
    )
    create_entry_group >> delete_entry_group
    delete_tag = DummyOperator(
        task_id="delete_tag",
        dag=dag,
    )
    create_tag >> delete_tag
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

    create_entry_group >> delete_entry_group
    create_entry_group >> create_entry_group_result
    create_entry_group >> create_entry_group_result2

    create_entry_gcs >> delete_entry
    create_entry_gcs >> create_entry_gcs_result
    create_entry_gcs >> create_entry_gcs_result2

    create_tag_template >> delete_tag_template_field
    create_tag_template >> create_tag_template_result
    create_tag_template >> create_tag_template_result2

    create_tag_template_field >> delete_tag_template_field
    create_tag_template_field >> create_tag_template_field_result
    create_tag_template_field >> create_tag_template_field_result2

    create_tag >> delete_tag
    create_tag >> create_tag_result
    create_tag >> create_tag_result2

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
    create_tag_template >> get_tag_template >> delete_tag_template
    get_tag_template >> get_tag_template_result

    create_entry_gcs >> get_entry >> delete_entry
    get_entry >> get_entry_result

    create_entry_group >> get_entry_group >> delete_entry_group
    get_entry_group >> get_entry_group_result

    # List
    create_tag >> list_tags >> delete_tag
    list_tags >> list_tags_result

    # Lookup
    create_entry_gcs >> lookup_entry >> delete_entry
    lookup_entry >> lookup_entry_result

    # Rename
    create_tag_template_field >> rename_tag_template_field >> delete_tag_template_field

    # Search
    chain(create_tasks, search_catalog, delete_tasks)
    search_catalog >> search_catalog_result

    # Update
    create_entry_gcs >> update_entry >> delete_entry
    create_tag >> update_tag >> delete_tag
    create_tag_template >> update_tag_template >> delete_tag_template
    create_tag_template_field >> update_tag_template_field >> rename_tag_template_field

    snapshot.assert_match(
        serialize_pp(
            PipelineSnapshot.from_pipeline_def(
                make_dagster_pipeline_from_airflow_dag(dag=dag)
            ).dep_structure_snapshot
        )
    )
