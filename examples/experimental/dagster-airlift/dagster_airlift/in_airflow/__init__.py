def ensure_airflow_installed() -> None:
    """Ensures that Airflow is installed."""
    try:
        import airflow  # noqa
    except ImportError:
        raise Exception(
            "Airflow is not installed. Please install Apache Airflow >= 2.0.0 before using this functionality."
            "Airflow has very specific installation instructions, please refer to the official installation guide: "
            "https://airflow.apache.org/docs/apache-airflow/stable/installation/installing-from-pypi.html"
        )


ensure_airflow_installed()
from .base_asset_operator import BaseDagsterAssetsOperator as BaseDagsterAssetsOperator
from .dag_proxy_operator import (
    BaseProxyDAGToDagsterOperator as BaseProxyDAGToDagsterOperator,
    DefaultProxyDAGToDagsterOperator as DefaultProxyDAGToDagsterOperator,
)
from .proxying_fn import proxying_to_dagster as proxying_to_dagster
from .task_proxy_operator import (
    BaseProxyTaskToDagsterOperator as BaseProxyTaskToDagsterOperator,
    DefaultProxyTaskToDagsterOperator as DefaultProxyTaskToDagsterOperator,
)
