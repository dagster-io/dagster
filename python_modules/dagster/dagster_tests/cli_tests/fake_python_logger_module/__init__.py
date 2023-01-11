import logging
import os

if not os.getenv("REQUIRED_LOGGER_ENV_VAR") == "LOGGER_ENV_VAR_VALUE":
    raise Exception("Missing env var REQUIRED_LOGGER_ENV_VAR")


class FakeHandler(logging.StreamHandler):
    pass
