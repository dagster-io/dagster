from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def build_final_defs() -> Definitions:
    from kitchen_sink.dagster_defs.print_defs import defs as print_defs

    return build_defs_from_airflow_instance(
        airflow_instance=airflow_instance,
        defs=Definitions.merge(
            print_defs,
        ),
    )


defs = build_final_defs()
