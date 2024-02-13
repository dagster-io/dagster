import base64
import json
import os
import tempfile
from contextlib import contextmanager

from dagster._core.errors import DagsterInvalidDefinitionError


@contextmanager
def setup_gcp_creds(gcp_creds: str):
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None:
        raise DagsterInvalidDefinitionError(
            "Resource config error: gcp_credentials config for BigQuery resource cannot"
            " be used if GOOGLE_APPLICATION_CREDENTIALS environment variable is set."
        )
    with tempfile.NamedTemporaryFile("w+") as f:
        temp_file_name = f.name
        json.dump(
            json.loads(base64.b64decode(gcp_creds)),
            f,
        )
        f.flush()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_name
        try:
            yield
        finally:
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
