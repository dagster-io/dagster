import json
import os
from contextlib import contextmanager
from threading import Event, Thread
from typing import TYPE_CHECKING, Iterator, Mapping

from dagster_externals import DAGSTER_EXTERNALS_ENV_KEYS

from dagster._utils import tail_file

if TYPE_CHECKING:
    from .task import ExternalExecutionTask


@contextmanager
def file_context_source(task: "ExternalExecutionTask", path: str) -> Iterator[Mapping[str, str]]:
    context_source_params = {"path": path}
    env = {DAGSTER_EXTERNALS_ENV_KEYS["context_source"]: json.dumps(context_source_params)}
    external_context = task.get_external_context()
    with open(path, "w") as input_stream:
        json.dump(external_context, input_stream)
    try:
        yield env
    finally:
        if os.path.exists(path):
            os.remove(path)


@contextmanager
def file_message_sink(task: "ExternalExecutionTask", path: str) -> Iterator[Mapping[str, str]]:
    message_sink_params = {"path": path}
    env = {DAGSTER_EXTERNALS_ENV_KEYS["message_sink"]: json.dumps(message_sink_params)}
    is_task_complete = Event()
    thread = None
    try:
        open(path, "w").close()  # create file
        thread = Thread(target=_read_messages, args=(task, path, is_task_complete), daemon=True)
        thread.start()
        yield env
    finally:
        is_task_complete.set()
        if os.path.exists(path):
            os.remove(path)
        if thread:
            thread.join()


def _read_messages(task: "ExternalExecutionTask", path: str, is_task_complete: Event) -> None:
    for line in tail_file(path, lambda: is_task_complete.is_set()):
        message = json.loads(line)
        task.handle_message(message)
