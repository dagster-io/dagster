import requests
from dagster_airlift.core import AirflowInstance
from dagster_airlift.core.basic_auth import AirflowAuthBackend


class DummyAuthBackend(AirflowAuthBackend):
    def get_session(self) -> requests.Session:
        raise NotImplementedError("This shouldn't be called from this mock context.")

    def get_webserver_url(self) -> str:
        return "http://dummy.domain"


class DummyInstance(AirflowInstance):
    def __init__(self) -> None:
        super().__init__(
            auth_backend=DummyAuthBackend(),
            name="dummy_instance",
        )
