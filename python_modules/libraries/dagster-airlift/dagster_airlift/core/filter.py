from collections.abc import Sequence
from typing import Optional

from dagster._record import record


@record
class AirflowFilter:
    """Filters the set of Airflow objects to fetch.

    Args:
        dag_id_ilike (Optional[str]): A pattern used to match the set of dag_ids to retrieve. Uses the sql ILIKE operator Airflow-side.
        airflow_tags (Optional[Sequence[str]]): Filters down to the set of Airflow DAGs whcih contain the particular tags provided.
        retrieve_datasets (bool): Whether to retrieve datasets from Airflow. Defaults to True.
        dataset_uri_ilike (Optional[str]): A pattern used to match the set of datasets to retrieve. Uses the sql ILIKE operator Airflow-side.
    """

    dag_id_ilike: Optional[str] = None
    airflow_tags: Optional[Sequence[str]] = None
    retrieve_datasets: bool = True
    dataset_uri_ilike: Optional[str] = None

    def augment_request_params(self, request_params: dict) -> dict:
        new_request_params = request_params.copy()
        if self.dag_id_ilike is not None:
            new_request_params["dag_id_pattern"] = self.dag_id_ilike
        if self.airflow_tags is not None:
            new_request_params["tags"] = self.airflow_tags
        return new_request_params
