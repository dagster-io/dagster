import threading
from typing import Tuple, cast

import dagster._check as check
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster._utils import send_interrupt


def _kill_on_cancel(instance_ref: InstanceRef, run_id, shutdown_event):
    check.inst_param(instance_ref, "instance_ref", InstanceRef)
    check.str_param(run_id, "run_id")

    with DagsterInstance.from_ref(instance_ref) as instance:
        while not shutdown_event.is_set():
            shutdown_event.wait(instance.cancellation_thread_poll_interval_seconds)
            run = cast(
                PipelineRun,
                check.inst(
                    instance.get_run_by_id(run_id),
                    PipelineRun,
                    "Run not found for cancellation thread",
                ),
            )
            if run.status in [
                PipelineRunStatus.CANCELING,
                PipelineRunStatus.CANCELED,
            ]:
                print(  # pylint: disable=print-call
                    f"Detected run status {run.status}, sending interrupt to main thread"
                )
                send_interrupt()
                return


def start_run_cancellation_thread(
    instance: DagsterInstance, run_id
) -> Tuple[threading.Thread, threading.Event]:
    print("Starting run cancellation thread")  # pylint: disable=print-call
    shutdown_event = threading.Event()
    thread = threading.Thread(
        target=_kill_on_cancel,
        args=(instance.get_ref(), run_id, shutdown_event),
        name="kill-on-cancel",
    )
    thread.start()
    return thread, shutdown_event
