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

from airflow import models

from airflow.utils.dates import days_ago
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.helpers import chain
from datetime import timedelta

default_args = {"start_date": days_ago(1), "retries": 3, "retry_delay": timedelta(minutes=1)}

with models.DAG(
    dag_id="example_complex", default_args=default_args, schedule_interval='* * * * *', tags=['example'],
) as complex_dag:

    # Create
    create_entry_group = BashOperator(
        task_id="create_entry_group", bash_command="echo create_entry_group", retries=0, retry_delay=timedelta(seconds=5)
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

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

args = {
    'owner': 'airflow',
    'start_date': days_ago(2),
}

bash_dag = DAG(
    dag_id='example_bash_operator',
    default_args=args,
    schedule_interval='0 0 * * *',
    dagrun_timeout=timedelta(minutes=60),
    tags=['example'],
)

run_this_last = DummyOperator(task_id='run_this_last', dag=bash_dag,)

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

if __name__ == "__main__":
    bash_dag.cli()
'''

COMBINED_FILE_CONTENTS = COMPLEX_DAG_FILE_CONTENTS + BASH_DAG_FILE_CONTENTS

test_make_from_dagbag_inputs = [
    ([("complex.py", COMPLEX_DAG_FILE_CONTENTS)], None, ["example_complex"]),
    ([("bash.py", BASH_DAG_FILE_CONTENTS)], None, ["example_bash_operator"]),
    (
        [
            ("complex.py", COMPLEX_DAG_FILE_CONTENTS),
            ("bash.py", BASH_DAG_FILE_CONTENTS),
        ],
        None,
        ["example_complex", "example_bash_operator"],
    ),
    (
        [("complex.py", COMPLEX_DAG_FILE_CONTENTS)],
        "complex.py",
        ["example_complex"],
    ),
    (
        [("bash.py", BASH_DAG_FILE_CONTENTS)],
        "bash.py",
        ["example_bash_operator"],
    ),
    (
        [("combined.py", COMBINED_FILE_CONTENTS)],
        None,
        ["example_complex", "example_bash_operator"],
    ),
]


COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2 = '''#
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
from datetime import timedelta

default_args = {"start_date": pendulum.today('UTC').add(days=-1), "retries": 3, "retry_delay": timedelta(minutes=1)}

with models.DAG(
    dag_id="example_complex", default_args=default_args, schedule='* * * * *', tags=['example'],
) as complex_dag:

    # Create
    create_entry_group = BashOperator(
        task_id="create_entry_group", bash_command="echo create_entry_group", retries=0, retry_delay=timedelta(seconds=5)
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

BASH_DAG_FILE_CONTENTS_AIRFLOW_2 = '''#
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

COMBINED_FILE_CONTENTS = COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2 + BASH_DAG_FILE_CONTENTS_AIRFLOW_2


test_make_from_dagbag_inputs_airflow_2 = [
    ([("complex.py", COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2)], None, ["example_complex"]),
    ([("bash.py", BASH_DAG_FILE_CONTENTS_AIRFLOW_2)], None, ["example_bash_operator"]),
    (
        [
            ("complex.py", COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2),
            ("bash.py", BASH_DAG_FILE_CONTENTS_AIRFLOW_2),
        ],
        None,
        ["example_complex", "example_bash_operator"],
    ),
    (
        [("complex.py", COMPLEX_DAG_FILE_CONTENTS_AIRFLOW_2)],
        "complex.py",
        ["example_complex"],
    ),
    (
        [("bash.py", BASH_DAG_FILE_CONTENTS_AIRFLOW_2)],
        "bash.py",
        ["example_bash_operator"],
    ),
    (
        [("combined.py", COMBINED_FILE_CONTENTS)],
        None,
        ["example_complex", "example_bash_operator"],
    ),
]
