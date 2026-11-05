"""Local QA transport that holds a production admission decision before Pod persistence."""

import argparse
import json
import threading
import time
from pathlib import Path
from typing import Literal

import kubernetes
from dagster import DagsterInstance
from dagster_k8s.backfill_admission import (
    ADMISSION_WEBHOOK_NAME,
    BackfillPodAdmission,
    PodAdmissionReview,
)
from dagster_k8s.backfill_admission_server import AdmissionHandler, AdmissionServer
from pydantic import BaseModel, Field, FilePath


class Settings(BaseModel):
    tls_cert: FilePath
    tls_key: FilePath
    mode: Literal["normal", "held-before", "held-after", "native-init-sidecars"]
    port: int = Field(default=8443, ge=1, le=65535)
    webhook_name: str = Field(
        min_length=1, max_length=63, pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
    )


class AdmissionControl:
    def __init__(self, mode: str):
        self.mode = mode
        self.lock = threading.Lock()
        self.release = threading.Event()
        self.held_uid: str | None = None
        self.events: list[dict] = []

    def record(self, event: str, uid: str, **values) -> None:
        data = {"event": event, "uid": uid, "observed_at": time.time(), **values}
        with self.lock:
            self.events.append(data)
        print("DAGSTER_ADMISSION_EVIDENCE=" + json.dumps(data, sort_keys=True), flush=True)

    def hold(self, review: PodAdmissionReview, phase: str) -> None:
        uid = str(review.request.uid)
        job = review.request.object.metadata.labels.get("dagster/worker-job", "")
        if self.mode != phase or not job.startswith("dagster-step-"):
            return
        with self.lock:
            if self.held_uid is not None:
                return
            self.held_uid = uid
        self.record("held", uid, phase=phase, job_name=job)
        # The Kubernetes admission timeout is 30 seconds. Release earlier so a
        # failed QA controller cannot leave an unbounded request in flight.
        released = self.release.wait(timeout=25)
        self.record("released" if released else "hold_timeout", uid)

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "mode": self.mode,
                "held_uid": self.held_uid,
                "released": self.release.is_set(),
                "events": list(self.events),
            }


class ControlledAdmission(BackfillPodAdmission):
    def __init__(self, instance, batch_api, control: AdmissionControl, webhook_name: str):
        super().__init__(instance, batch_api, webhook_name)
        self.control = control

    def admit(self, review: PodAdmissionReview) -> dict:
        uid = str(review.request.uid)
        self.control.hold(review, "held-before")
        try:
            response = super().admit(review)
        except Exception as error:
            self.control.record("decision_error", uid, error_type=type(error).__name__)
            raise
        self.control.record("decision", uid, allowed=response["allowed"])
        if response["allowed"]:
            self.control.hold(review, "held-after")
        return response


class ControlledHandler(AdmissionHandler):
    def do_GET(self):
        if self.path != "/qa/status":
            return super().do_GET()
        self.respond(self.server.control.snapshot())

    def do_POST(self):
        if self.path != "/qa/release":
            return super().do_POST()
        self.server.control.release.set()
        self.respond(self.server.control.snapshot())

    def respond(self, value: dict) -> None:
        payload = json.dumps(value, sort_keys=True).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class ControlledServer(AdmissionServer):
    def __init__(self, admission, settings: Settings, control: AdmissionControl):
        self.control = control
        super().__init__(("0.0.0.0", settings.port), admission, settings.tls_cert, settings.tls_key)
        self.RequestHandlerClass = ControlledHandler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tls-cert", type=Path, required=True)
    parser.add_argument("--tls-key", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("normal", "held-before", "held-after", "native-init-sidecars"),
        default="normal",
    )
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--webhook-name", default=ADMISSION_WEBHOOK_NAME)
    settings = Settings.model_validate(vars(parser.parse_args()))
    kubernetes.config.load_incluster_config()
    control = AdmissionControl(settings.mode)
    with DagsterInstance.get() as instance:
        instance.upgrade()
        admission = ControlledAdmission(
            instance, kubernetes.client.BatchV1Api(), control, settings.webhook_name
        )
        with ControlledServer(admission, settings, control) as server:
            server.serve_forever()


if __name__ == "__main__":
    main()
