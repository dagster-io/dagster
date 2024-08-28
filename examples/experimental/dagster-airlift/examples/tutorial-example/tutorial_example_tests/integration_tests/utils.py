import time

import requests
from dagster._time import get_current_timestamp


def start_run_and_wait_for_completion(dag_id: str) -> None:
    response = requests.post(
        f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns", auth=("admin", "admin"), json={}
    )
    assert response.status_code == 200, response.json()
    # Wait until the run enters a terminal state
    terminal_status = None
    start_time = get_current_timestamp()
    while get_current_timestamp() - start_time < 30:
        response = requests.get(
            f"http://localhost:8080/api/v1/dags/{dag_id}/dagRuns", auth=("admin", "admin")
        )
        assert response.status_code == 200, response.json()
        dag_runs = response.json()["dag_runs"]
        if dag_runs[0]["state"] in ["success", "failed"]:
            terminal_status = dag_runs[0]["state"]
            break
        time.sleep(1)
    assert terminal_status == "success", (
        "Never reached terminal status"
        if terminal_status is None
        else f"terminal status was {terminal_status}"
    )
