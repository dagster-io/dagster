#!/usr/bin/env python3

import os
import re
import subprocess
import sys
import tempfile
import time

MAX_RETRIES = 5
DELAY = 3

TRANSIENT_ERRORS = [
    re.compile(r"stream closed because of a broken pipe", re.IGNORECASE),
    re.compile(r"connection reset", re.IGNORECASE),
]


def has_transient_error(log_text):
    return any(pattern.search(log_text) for pattern in TRANSIENT_ERRORS)


def main():
    args = ["uv", "pip", "install"] + sys.argv[1:]

    for attempt in range(1, MAX_RETRIES + 1):
        log_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as log_file:
                log_path = log_file.name
                subprocess.run(
                    args,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    check=True,
                    text=True,
                )
            os.remove(log_path)
            return 0

        except subprocess.CalledProcessError:
            if log_path:
                with open(log_path) as f:
                    log_contents = f.read()
                os.remove(log_path)

                if has_transient_error(log_contents):
                    time.sleep(DELAY)
                    continue
                else:
                    print(log_contents)  # noqa
                    return 1

        except Exception:
            if log_path and os.path.exists(log_path):
                os.remove(log_path)
            raise

    return 1


if __name__ == "__main__":
    sys.exit(main())
