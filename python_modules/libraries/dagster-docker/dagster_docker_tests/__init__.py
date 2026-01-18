import os

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
