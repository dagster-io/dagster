"""
The airflow DAG scaffold for docs_snippets.intro_tutorial.airflow.hello_cereal_pipeline

Note that this docstring must contain the strings "airflow" and "DAG" for
Airflow to properly detect it as a DAG
See: http://bit.ly/307VMum
"""
import datetime

import yaml
from dagster_airflow.factory import make_airflow_dag

################################################################################
# #
# # This environment is auto-generated from your configs and/or presets
# #
################################################################################
ENVIRONMENT = """
storage:
  filesystem:
    config:
      base_dir: /tmp/dagster-airflow/hello_cereal_pipeline

"""


################################################################################
# #
# # NOTE: these arguments should be edited for your environment
# #
################################################################################
DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2019, 11, 7),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

dag, tasks = make_airflow_dag(
    # NOTE: you must ensure that docs_snippets.intro_tutorial.airflow is
    # installed or available on sys.path, otherwise, this import will fail.
    module_name="docs_snippets.intro_tutorial.airflow",
    pipeline_name="hello_cereal_pipeline",
    run_config=yaml.safe_load(ENVIRONMENT),
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1},
)
