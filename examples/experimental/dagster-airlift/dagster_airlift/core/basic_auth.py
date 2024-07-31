import requests

from .airflow_instance import AirflowAuthBackend


class BasicAuthBackend(AirflowAuthBackend):
    def __init__(self, webserver_url: str, username: str, password: str):
        self._webserver_url = webserver_url
        self.username = username
        self.password = password

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (self.username, self.password)
        return session

    def get_webserver_url(self) -> str:
        return self._webserver_url
