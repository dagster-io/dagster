"""TLS transport for durable backfill Pod admission."""

import argparse
import json
import logging
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

import kubernetes
from dagster import DagsterInstance
from pydantic import BaseModel, Field, FilePath

from dagster_k8s.backfill_admission import (
    ADMISSION_WEBHOOK_NAME,
    BackfillPodAdmission,
    PodAdmissionReview,
)


class AdmissionServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, admission: BackfillPodAdmission, certificate: Path, key: Path):
        self.admission = admission
        self.certificate = certificate
        self.key = key
        super().__init__(address, AdmissionHandler)

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        # Loading on each connection follows projected certificate rotation without a restart.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(self.certificate, self.key)
        return context.wrap_socket(connection, server_side=True), address


class AdmissionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path != "/healthz":
            self.send_error(404)
            return
        ready = cast(
            "AdmissionServer", self.server
        ).admission.instance.supports_backfill_stop_protocol
        self.send_response(200 if ready else 503)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if urlsplit(self.path).path != "/admit":
            self.send_error(404)
            return
        uid = ""
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 3 * 1024 * 1024:
                raise ValueError("Invalid request size")
            review = PodAdmissionReview.model_validate_json(self.rfile.read(length))
            uid = str(review.request.uid)
            response = cast("AdmissionServer", self.server).admission.admit(review)
        except Exception as error:
            # Admission objects contain worker arguments and instance credentials.
            logging.getLogger("dagster_k8s.admission").error(
                "Pod admission failed (%s)", type(error).__name__
            )
            response = {"uid": uid, "allowed": False, "status": {"message": "Pod admission failed"}}
        payload = json.dumps(
            {"apiVersion": "admission.k8s.io/v1", "kind": "AdmissionReview", "response": response}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):  # noqa: A002
        return


class AdmissionSettings(BaseModel):
    port: int = Field(default=8443, ge=1, le=65535)
    tls_cert: FilePath
    tls_key: FilePath
    webhook_name: str = Field(
        default=ADMISSION_WEBHOOK_NAME,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--tls-cert", type=Path, required=True)
    parser.add_argument("--tls-key", type=Path, required=True)
    parser.add_argument("--webhook-name", default=ADMISSION_WEBHOOK_NAME)
    args = AdmissionSettings.model_validate(vars(parser.parse_args()))
    kubernetes.config.load_incluster_config()
    with DagsterInstance.get() as instance:
        admission = BackfillPodAdmission(
            instance, kubernetes.client.BatchV1Api(), args.webhook_name
        )
        with AdmissionServer(
            ("0.0.0.0", args.port), admission, args.tls_cert, args.tls_key
        ) as server:
            server.serve_forever()


if __name__ == "__main__":
    main()
