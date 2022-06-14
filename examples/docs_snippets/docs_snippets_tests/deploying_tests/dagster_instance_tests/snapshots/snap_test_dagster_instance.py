# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_instance_yaml 1"] = [
    "code_servers",
    "compute_logs",
    "local_artifact_storage",
    "run_coordinator",
    "run_launcher",
    "run_monitoring",
    "run_retries",
    "storage",
    "telemetry",
]
