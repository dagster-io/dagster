import logging
import os
import sys
from contextlib import contextmanager
from typing import Generator, List, Mapping, Optional

from airflow import __version__ as airflow_version
from airflow.models.connection import Connection
from airflow.settings import LOG_FORMAT
from dagster._core.definitions.utils import VALID_NAME_REGEX
from packaging import version


def is_airflow_2_loaded_in_environment(version_to_check: str = "2.0.0") -> bool:
    # in sphinx context, airflow.__version__ is set to
    # this string, version.parse errors trying to parse it
    if str(airflow_version) == "airflow.__version__":
        return False
    return version.parse(str(airflow_version)) >= version.parse(version_to_check)


if is_airflow_2_loaded_in_environment():
    from airflow.utils.session import create_session
else:
    from airflow.utils.db import create_session


class DagsterAirflowError(Exception):
    pass


def create_airflow_connections(connections: List[Connection] = []) -> None:
    with create_session() as session:
        for connection in connections:
            if session.query(Connection).filter(Connection.conn_id == connection.conn_id).first():
                logging.info(
                    f"Could not import connection {connection.conn_id}: connection already exists."
                )
                continue

            session.add(connection)
            session.commit()
            logging.info(f"Imported connection {connection.conn_id}")


# Airflow DAG ids and Task ids allow a larger valid character set (alphanumeric characters,
# dashes, dots and underscores) than Dagster's naming conventions (alphanumeric characters,
# underscores), so Dagster will strip invalid characters and replace with '_'
def normalized_name(dag_name, task_name=None) -> str:
    base_name = "".join(c if VALID_NAME_REGEX.match(c) else "_" for c in dag_name)
    if task_name:
        base_name += "__"
        base_name += "".join(c if VALID_NAME_REGEX.match(c) else "_" for c in task_name)
    return base_name


@contextmanager
def replace_airflow_logger_handlers() -> Generator[None, None, None]:
    prev_airflow_handlers = logging.getLogger("airflow.task").handlers
    try:
        # Redirect airflow handlers to stdout / compute logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root = logging.getLogger("airflow.task")
        root.handlers = [handler]
        yield
    finally:
        # Restore previous log handlers
        logging.getLogger("airflow.task").handlers = prev_airflow_handlers


def serialize_connections(connections: List[Connection] = []) -> List[Mapping[str, Optional[str]]]:
    serialized_connections = []
    for c in connections:
        serialized_connection = {
            "conn_id": c.conn_id,
            "conn_type": c.conn_type,
        }
        if hasattr(c, "login") and c.login:
            serialized_connection["login"] = c.login
        if hasattr(c, "password") and c.password:
            serialized_connection["password"] = c.password
        if hasattr(c, "host") and c.host:
            serialized_connection["host"] = c.host
        if hasattr(c, "schema") and c.schema:
            serialized_connection["schema"] = c.schema
        if hasattr(c, "port") and c.port:
            serialized_connection["port"] = c.port
        if hasattr(c, "extra") and c.extra:
            serialized_connection["extra"] = c.extra
        if hasattr(c, "description") and c.description:
            serialized_connection["description"] = c.description
        serialized_connections.append(serialized_connection)
    return serialized_connections


if os.name == "nt":
    import msvcrt

    def portable_lock(fp):
        fp.seek(0)
        msvcrt.locking(fp.fileno(), msvcrt.LK_LOCK, 1)

    def portable_unlock(fp):
        fp.seek(0)
        msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def portable_lock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)

    def portable_unlock(fp):
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


class Locker:
    def __init__(self, lock_file_path="."):
        self.lock_file_path = lock_file_path
        self.fp = None

    def __enter__(self):
        self.fp = open(f"{self.lock_file_path}/lockfile.lck", "w+", encoding="utf-8")
        portable_lock(self.fp)

    def __exit__(self, _type, value, tb):
        portable_unlock(self.fp)
        self.fp.close() if self.fp else None
