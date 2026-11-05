"""A local native init sidecar that restarts once, then runs until Pod termination."""

import time
from pathlib import Path

marker = Path("/proof/restarted")
if not marker.exists():
    marker.write_text("restart requested\n", encoding="utf-8")
    print("NATIVE_INIT_SIDECAR_INTENTIONAL_RESTART", flush=True)
    time.sleep(2)
    raise SystemExit(17)

print("NATIVE_INIT_SIDECAR_RUNNING", flush=True)
while True:
    time.sleep(0.1)
