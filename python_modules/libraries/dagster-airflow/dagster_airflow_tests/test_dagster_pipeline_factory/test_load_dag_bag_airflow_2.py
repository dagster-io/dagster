import os
import tempfile

import pytest
from airflow import __version__ as airflow_version
from dagster_airflow.dagster_pipeline_factory import (
    make_dagster_repo_from_airflow_dags_path,
    make_dagster_repo_from_airflow_example_dags,
)
from dagster_airflow_tests.marks import requires_airflow_db

COMPLEX_DAG_FILE_CONTENTS = '''#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Example Airflow DAG that shows the complex DAG structure.
"""
import sys
import pendulum

from airflow import models

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain

default_args = {"start_date": pendulum.today('UTC').add(days=-1)}

with models.DAG(
    dag_id="example_complex", default_args=default_args, schedule=None, tags=['example'],
) as complex_dag:

    # Create
    create_entry_group = BashOperator(
        task_id="create_entry_group", bash_command="echo create_entry_group"
    )

    create_entry_group_result = BashOperator(
        task_id="create_entry_group_result", bash_command="echo create_entry_group_result"
    )

    create_entry_group_result2 = BashOperator(
        task_id="create_entry_group_result2", bash_command="echo create_entry_group_result2"
    )

    create_entry_gcs = BashOperator(
        task_id="create_entry_gcs", bash_command="echo create_entry_gcs"
    )

    create_entry_gcs_result = BashOperator(
        task_id="create_entry_gcs_result", bash_command="echo create_entry_gcs_result"
    )

    create_entry_gcs_result2 = BashOperator(
        task_id="create_entry_gcs_result2", bash_command="echo create_entry_gcs_result2"
    )

    create_tag = BashOperator(task_id="create_tag", bash_command="echo create_tag")

    create_tag_result = BashOperator(
        task_id="create_tag_result", bash_command="echo create_tag_result"
    )

    create_tag_result2 = BashOperator(
        task_id="create_tag_result2", bash_command="echo create_tag_result2"
    )

    create_tag_template = BashOperator(
        task_id="create_tag_template", bash_command="echo create_tag_template"
    )

    create_tag_template_result = BashOperator(
        task_id="create_tag_template_result", bash_command="echo create_tag_template_result"
    )

    create_tag_template_result2 = BashOperator(
        task_id="create_tag_template_result2", bash_command="echo create_tag_template_result2"
    )

    create_tag_template_field = BashOperator(
        task_id="create_tag_template_field", bash_command="echo create_tag_template_field"
    )

    create_tag_template_field_result = BashOperator(
        task_id="create_tag_template_field_result",
        bash_command="echo create_tag_template_field_result",
    )

    create_tag_template_field_result2 = BashOperator(
        task_id="create_tag_template_field_result2",
        bash_command="echo create_tag_template_field_result2",
    )

    # Delete
    delete_entry = BashOperator(task_id="delete_entry", bash_command="echo delete_entry")
    create_entry_gcs >> delete_entry

    delete_entry_group = BashOperator(
        task_id="delete_entry_group", bash_command="echo delete_entry_group"
    )
    create_entry_group >> delete_entry_group

    delete_tag = BashOperator(task_id="delete_tag", bash_command="echo delete_tag")
    create_tag >> delete_tag

    delete_tag_template_field = BashOperator(
        task_id="delete_tag_template_field", bash_command="echo delete_tag_template_field"
    )

    delete_tag_template = BashOperator(
        task_id="delete_tag_template", bash_command="echo delete_tag_template"
    )

    # Get
    get_entry_group = BashOperator(task_id="get_entry_group", bash_command="echo get_entry_group")

    get_entry_group_result = BashOperator(
        task_id="get_entry_group_result", bash_command="echo get_entry_group_result"
    )

    get_entry = BashOperator(task_id="get_entry", bash_command="echo get_entry")

    get_entry_result = BashOperator(
        task_id="get_entry_result", bash_command="echo get_entry_result"
    )

    get_tag_template = BashOperator(
        task_id="get_tag_template", bash_command="echo get_tag_template"
    )

    get_tag_template_result = BashOperator(
        task_id="get_tag_template_result", bash_command="echo get_tag_template_result"
    )

    # List
    list_tags = BashOperator(task_id="list_tags", bash_command="echo list_tags")

    list_tags_result = BashOperator(
        task_id="list_tags_result", bash_command="echo list_tags_result"
    )

    # Lookup
    lookup_entry = BashOperator(task_id="lookup_entry", bash_command="echo lookup_entry")

    lookup_entry_result = BashOperator(
        task_id="lookup_entry_result", bash_command="echo lookup_entry_result"
    )

    # Rename
    rename_tag_template_field = BashOperator(
        task_id="rename_tag_template_field", bash_command="echo rename_tag_template_field"
    )

    # Search
    search_catalog = PythonOperator(
        task_id="search_catalog", python_callable=lambda: sys.stdout.write("search_catalog\\n")
    )

    search_catalog_result = BashOperator(
        task_id="search_catalog_result", bash_command="echo search_catalog_result"
    )

    # Update
    update_entry = BashOperator(task_id="update_entry", bash_command="echo update_entry")

    update_tag = BashOperator(task_id="update_tag", bash_command="echo update_tag")

    update_tag_template = BashOperator(
        task_id="update_tag_template", bash_command="echo update_tag_template"
    )

    update_tag_template_field = BashOperator(
        task_id="update_tag_template_field", bash_command="echo update_tag_template_field"
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
'''

BASH_DAG_FILE_CONTENTS = '''#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Example DAG demonstrating the usage of the BashOperator."""
# DAG
# airflow
from datetime import timedelta
import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

args = {
    'owner': 'airflow',
    'start_date': pendulum.today('UTC').add(days=-2),
}

bash_dag = DAG(
    dag_id='example_bash_operator',
    default_args=args,
    schedule='0 0 * * *',
    dagrun_timeout=timedelta(minutes=60),
    tags=['example'],
)

run_this_last = EmptyOperator(task_id='run_this_last', dag=bash_dag,)

# [START howto_operator_bash]
run_this = BashOperator(task_id='run_after_loop', bash_command='echo 1', dag=bash_dag,)
# [END howto_operator_bash]

run_this >> run_this_last

for i in range(3):
    task = BashOperator(
        task_id='runme_' + str(i),
        bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
        dag=bash_dag,
    )
    task >> run_this

# [START howto_operator_bash_template]
also_run_this = BashOperator(
    task_id='also_run_this',
    bash_command='echo "run_id={{ run_id }} | dag_run={{ dag_run }}"',
    dag=bash_dag,
)
# [END howto_operator_bash_template]
also_run_this >> run_this_last
'''

COMBINED_FILE_CONTENTS = COMPLEX_DAG_FILE_CONTENTS + BASH_DAG_FILE_CONTENTS

test_make_repo_inputs = [
    ([("complex.py", COMPLEX_DAG_FILE_CONTENTS)], None, ["airflow_example_complex"]),
    ([("bash.py", BASH_DAG_FILE_CONTENTS)], None, ["airflow_example_bash_operator"]),
    (
        [
            ("complex.py", COMPLEX_DAG_FILE_CONTENTS),
            ("bash.py", BASH_DAG_FILE_CONTENTS),
        ],
        None,
        ["airflow_example_complex", "airflow_example_bash_operator"],
    ),
    (
        [("complex.py", COMPLEX_DAG_FILE_CONTENTS)],
        "complex.py",
        ["airflow_example_complex"],
    ),
    (
        [("bash.py", BASH_DAG_FILE_CONTENTS)],
        "bash.py",
        ["airflow_example_bash_operator"],
    ),
    (
        [("combined.py", COMBINED_FILE_CONTENTS)],
        None,
        ["airflow_example_complex", "airflow_example_bash_operator"],
    ),
]


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@pytest.mark.parametrize(
    "path_and_content_tuples, fn_arg_path, expected_job_names",
    test_make_repo_inputs,
)
def test_make_repo(
    path_and_content_tuples,
    fn_arg_path,
    expected_job_names,
):
    repo_name = "my_repo_name"
    with tempfile.TemporaryDirectory() as tmpdir_path:
        for (path, content) in path_and_content_tuples:
            with open(os.path.join(tmpdir_path, path), "wb") as f:
                f.write(bytes(content.encode("utf-8")))

        repo = (
            make_dagster_repo_from_airflow_dags_path(
                tmpdir_path,
                repo_name,
            )
            if fn_arg_path is None
            else make_dagster_repo_from_airflow_dags_path(
                os.path.join(tmpdir_path, fn_arg_path), repo_name
            )
        )

        for job_name in expected_job_names:
            assert repo.name == repo_name
            assert repo.has_job(job_name)

            job = repo.get_job(job_name)
            result = job.execute_in_process()
            assert result.success
            for event in result.all_events:
                assert event.event_type_value != "STEP_FAILURE"

        assert set(repo.job_names) == set(expected_job_names)


@pytest.fixture(scope="module")
def airflow_examples_repo():
    return make_dagster_repo_from_airflow_example_dags()


def get_examples_airflow_repo_params():
    repo = make_dagster_repo_from_airflow_example_dags()
    assert repo.name == "airflow_example_dags_repo"
    params = []
    no_job_run_dags = [
        # requires k8s environment to work
        # FileNotFoundError: [Errno 2] No such file or directory: '/foo/volume_mount_test.txt'
        "airflow_example_kubernetes_executor",
        # requires params to be passed in to work
        "airflow_example_passing_params_via_test_command",
        # requires template files to exist
        "airflow_example_python_operator",
        # requires email server to work
        "airflow_example_dag_decorator",
        # airflow.exceptions.DagNotFound: Dag id example_trigger_target_dag not found in DagModel
        "airflow_example_trigger_target_dag",
        "airflow_example_trigger_controller_dag",
        # runs slow
        "airflow_example_subdag_operator",
        # runs slow
        "airflow_example_sensors",
    ]
    for job_name in repo.job_names:
        params.append(
            pytest.param(job_name, True if job_name in no_job_run_dags else False, id=job_name),
        )

    return params


@pytest.mark.skipif(airflow_version < "2.0.0", reason="requires airflow 2")
@pytest.mark.parametrize(
    "job_name, exclude_from_execution_tests",
    get_examples_airflow_repo_params(),
)
@requires_airflow_db
def test_airflow_example_dags(
    airflow_examples_repo,
    job_name,
    exclude_from_execution_tests,
):
    assert airflow_examples_repo.has_job(job_name)
    if not exclude_from_execution_tests:
        job = airflow_examples_repo.get_job(job_name)
        result = job.execute_in_process()
        assert result.success
        for event in result.all_events:
            assert event.event_type_value != "STEP_FAILURE"
