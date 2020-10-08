import os
import subprocess

import pytest
import six

from dagster.seven import get_system_temp_directory
from dagster.utils import mkdir_p


@pytest.fixture(scope="session")
def events_jar():
    git_repo_root = six.ensure_str(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()
    )

    temp_dir = os.path.join(
        get_system_temp_directory(), "dagster_examples_tests", "event_pipeline_demo_tests"
    )

    mkdir_p(temp_dir)
    dst = os.path.join(temp_dir, "events.jar")

    if os.path.exists(dst):
        print("events jar already exists, skipping")  # pylint: disable=print-call
    else:
        subprocess.check_call(
            ["sbt", "events/assembly"], cwd=os.path.join(git_repo_root, "scala_modules")
        )

        src = os.path.join(
            git_repo_root,
            "scala_modules",
            "events/target/scala-2.11/events-assembly-0.1.0-SNAPSHOT.jar",
        )
        subprocess.check_call(["cp", src, dst])

    yield dst


@pytest.fixture(scope="session")
def spark_home():
    spark_home_already_set = os.getenv("SPARK_HOME") is not None

    try:
        if not spark_home_already_set:
            try:
                import pyspark

                os.environ["SPARK_HOME"] = os.path.dirname(pyspark.__file__)

            # We don't have pyspark on this machine, and no spark home set, so there's nothing we
            # can do. Just give up - this fixture will end up yielding None
            except ModuleNotFoundError:
                pass

        yield os.getenv("SPARK_HOME")

    finally:
        # we set it, so clean up after ourselves
        if not spark_home_already_set and "SPARK_HOME" in os.environ:
            del os.environ["SPARK_HOME"]
