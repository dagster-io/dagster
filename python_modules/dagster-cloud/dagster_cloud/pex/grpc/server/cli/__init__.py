import logging
import os
import signal
import subprocess

from dagster._serdes import deserialize_value
from dagster._utils.interrupts import setup_interrupt_handlers
from dagster_cloud_cli.core.workspace import PexMetadata
from typer import Option, Typer

from dagster_cloud.pex.grpc.server.registry import PexS3Registry
from dagster_cloud.pex.grpc.server.server import run_multipex_server

app = Typer(hidden=True)


@app.command(short_help="Run multi-pex server to spin up subprocesses via PEX files")
def grpc(
    host: str = Option(default="localhost"),
    port: int | None = Option(default=None),
    socket: str | None = Option(default=None),
    max_workers: int | None = Option(default=None),
    local_pex_files_dir: str | None = Option(
        default="/tmp/pex-files", envvar="LOCAL_PEX_FILES_DIR"
    ),
    watchdog_run_interval: int | None = Option(default=30, envvar="WATCHDOG_RUN_INTERVAL"),
    enable_metrics: bool = Option(default=False, envvar="PEX_ENABLE_METRICS"),
):
    logger = logging.getLogger("dagster.multipex_server")

    run_multipex_server(
        port=port,
        socket=socket,
        host=host,
        logger=logger,
        max_workers=max_workers,
        local_pex_files_dir=local_pex_files_dir,
        watchdog_run_interval=watchdog_run_interval,
        enable_metrics=enable_metrics,
    )


@app.command(short_help="Execute a run with a PEX file")
def execute_run(
    input_json: str,
    pex_metadata_json: str,
    local_pex_files_dir: str | None = Option(
        default="/tmp/pex-files", envvar="LOCAL_PEX_FILES_DIR"
    ),
):
    setup_interrupt_handlers()
    pex_metadata = deserialize_value(pex_metadata_json, PexMetadata)
    executable = PexS3Registry(local_pex_files_dir).get_pex_executable(pex_metadata)

    run_process = subprocess.Popen(
        [
            executable.source_path,
            "-m",
            "dagster",
            "api",
            "execute_run",
            input_json,
        ],
        env={**os.environ.copy(), **executable.environ},
        cwd=executable.working_directory,
    )

    logger = logging.getLogger("dagster.pex_run")

    try:
        return_code = run_process.wait()
        if return_code != 0:
            raise Exception(f"PEX subprocess returned with exit code {return_code}")
    except KeyboardInterrupt:
        logger.info("Forwarding interrupt to PEX subprocess")
        run_process.send_signal(signal.SIGINT)
        run_process.wait()
        raise
