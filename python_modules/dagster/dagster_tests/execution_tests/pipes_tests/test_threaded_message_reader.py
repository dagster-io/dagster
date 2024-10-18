import json
import os
import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator, Optional, TextIO, Tuple

from dagster import AssetExecutionContext, AssetKey, asset, materialize
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.pipes.utils import (
    PipesChunkedLogReader,
    PipesEnvContextInjector,
    PipesLaunchedData,
    PipesParams,
    PipesThreadedMessageReader,
    open_pipes_session,
)
from dagster_pipes import PipesDefaultMessageWriter, _make_message


class PipesFileLogReader(PipesChunkedLogReader):
    def __init__(self, *, path: str, interval: float = 10, target_stream: TextIO):
        super().__init__(interval=interval, target_stream=target_stream)

        self.path = path
        self.file_position = 0

    def target_is_readable(self, params: PipesParams) -> bool:
        return os.path.exists(self.path)

    def download_log_chunk(self, params: PipesParams) -> str:
        with open(self.path, "r") as file:
            file.seek(self.file_position)
            chunk = file.read()
            self.file_position = file.tell()
            return chunk


class PipesFileMessageReader(PipesThreadedMessageReader):
    def __init__(self, *, log_readers, path: Optional[str] = None):
        self.path = path
        self.file_position = 0

        super().__init__(log_readers=log_readers)

    def on_launched(self, launched_payload: PipesLaunchedData) -> None:
        if "path" in launched_payload.get("extras", {}):
            self.path = launched_payload["extras"]["path"]

        super().on_launched(launched_payload)

    def messages_are_readable(self, params: PipesParams) -> bool:
        if self.path is not None:
            return os.path.exists(self.path)
        else:
            return False

    @contextmanager
    def get_params(self) -> Iterator[PipesParams]:
        yield {PipesDefaultMessageWriter.STDIO_KEY: PipesDefaultMessageWriter.STDOUT}

    def download_messages(
        self, cursor: Optional[int], params: PipesParams
    ) -> Optional[Tuple[int, str]]:
        if cursor is None:
            cursor = 0

        assert self.path is not None

        with open(self.path, "r") as file:
            file.seek(cursor)
            chunk = file.read()
            if chunk:
                return (file.tell(), chunk)

    def no_messages_debug_text(self) -> str:
        return "Attempted to read messages by extracting them from a file." ""


def test_file_log_reader(tmp_path_factory, capsys):
    logs_dir = tmp_path_factory.mktemp("logs")

    log_path = os.path.join(logs_dir, "test.log")

    reader = PipesFileLogReader(path=log_path, target_stream=sys.stdout)

    is_session_closed = threading.Event()

    assert not reader.target_is_readable({}), "Should not be able to read without the file existing"

    with open(log_path, "w") as file:
        file.write("1\n")

    assert reader.target_is_readable({}), "Should be able to read after the file was created"

    reader.start({}, is_session_closed)

    with open(log_path, "a") as file:
        file.write("2\n")
        file.write("3\n")

    is_session_closed.set()

    reader.stop()

    time.sleep(1)

    assert capsys.readouterr().out == "1\n2\n3\n"


def test_file_message_reader(tmp_path_factory, capsys):
    logs_dir = tmp_path_factory.mktemp("logs")

    messages_path = os.path.join(logs_dir, "messages.txt")
    log_path_1 = os.path.join(logs_dir, "test_1.log")
    log_path_2 = os.path.join(logs_dir, "test_2.log")

    log_path_3 = os.path.join(logs_dir, "test_3.log")

    log_reader_1 = PipesFileLogReader(
        path=log_path_1,
        target_stream=sys.stdout,
    )
    log_reader_2 = PipesFileLogReader(
        path=log_path_2,
        target_stream=sys.stderr,
    )

    # this one is used to test delayed PipesLogReader submission
    log_reader_3 = PipesFileLogReader(
        path=log_path_3,
        target_stream=sys.stderr,
    )

    reader = PipesFileMessageReader(
        log_readers=[
            log_reader_1,
            log_reader_2,
        ]
    )

    @asset
    def my_asset(context: AssetExecutionContext):
        with open_pipes_session(
            context=context, message_reader=reader, context_injector=PipesEnvContextInjector()
        ) as session:
            assert not reader.messages_are_readable({})

            new_params = {
                "path": messages_path,
            }

            session.report_launched({"extras": new_params})

            def log_event(message: str):
                with open(messages_path, "a") as file:
                    file.write(message + "\n")

            def log_line_1(message: str):
                with open(log_path_1, "a") as file:
                    file.write(message + "\n")

            def log_line_2(message: str):
                with open(log_path_2, "a") as file:
                    file.write(message + "\n")

            def log_line_3(message: str):
                with open(log_path_3, "a") as file:
                    file.write(message + "\n")

            log_line_1("Hello 1")

            log_event(json.dumps(_make_message(method="opened", params={})))

            assert reader.messages_are_readable({})

            log_event(
                json.dumps(
                    _make_message(method="log", params={"message": "Hello!", "level": "INFO"})
                )
            )

            log_event(
                json.dumps(
                    _make_message(
                        method="report_asset_materialization",
                        params={
                            "asset_key": "my_asset",
                            "metadata": {"foo": {"raw_value": "bar", "type": "text"}},
                            "data_version": "alpha",
                        },
                    )
                )
            )

            log_event(json.dumps(_make_message(method="closed", params={})))

            log_line_1("Bye 1")

            log_line_2("Hello 2")
            log_line_2("Bye 2")

            log_line_3("Hello 3")

            reader.add_log_reader(log_reader_3)

            log_line_3("Bye 3")

        return session.get_results()

    result = materialize([my_asset])

    assert result.success

    mats = result.get_asset_materialization_events()
    assert len(mats) == 1
    mat = mats[0]
    assert mat.asset_key == AssetKey(["my_asset"])
    assert mat.materialization.metadata["foo"].value == "bar"
    assert mat.materialization.tags[DATA_VERSION_TAG] == "alpha"

    captured = capsys.readouterr()

    assert "Hello 1" in captured.out
    assert "Bye 1" in captured.out

    assert "Hello 2" in captured.err
    assert "Bye 2" in captured.err

    assert "Hello 3" in captured.err
    assert "Bye 3" in captured.err
