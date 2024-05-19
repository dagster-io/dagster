from typing import Optional

raise Exception("get here")
from fastapi import APIRouter, FastAPI

from dagster._core.instance import DagsterInstance
from dagster._deployment.in_memory_server import InMemoryDeploymentServer
from dagster._deployment.interface import FetchRunEventRecordsResponse, IDeploymentServer

app = FastAPI()
router = APIRouter(prefix="/rest/v1")


class FastAPIDeploymentServer(IDeploymentServer):
    def __init__(self, *, app: FastAPI, instance: DagsterInstance) -> None:
        self._app = app
        self._server = InMemoryDeploymentServer(instance=instance)

    @router.get("/run_event_records/{run_id}")
    def fetch_event_records_for_run(
        self, *, run_id: str, cursor: Optional[str] = None, limit: int = 100, ascending: bool = True
    ) -> FetchRunEventRecordsResponse:
        return self._server.fetch_event_records_for_run(
            run_id=run_id, cursor=cursor, limit=limit, ascending=ascending
        )


if __name__ == "__main__":
    deployment_api = FastAPIDeploymentServer(app=app, instance=DagsterInstance.get())
    app.include_router(router)
