from collections.abc import Sequence
from typing import Optional

from dagster._record import record


@record
class AirflowFilter:
    dag_id_ilike: Optional[str] = None
    airflow_tags: Optional[Sequence[str]] = None
    include_paused: bool = False
    include_inactive: bool = True

    def augment_request_params(self, request_params: dict) -> dict:
        new_request_params = request_params.copy()
        if self.dag_id_ilike is not None:
            new_request_params["dag_id_pattern"] = self.dag_id_ilike
        if self.airflow_tags is not None:
            new_request_params["tags"] = self.airflow_tags
        if not self.include_inactive:
            new_request_params["only_active"] = "true"
        return new_request_params

    def augment_request_body(self, request_body: dict) -> dict:
        new_request_body = request_body.copy()
        if self.include_paused:
            new_request_body["is_paused"] = "true"
        return new_request_body
