import os
import subprocess

import dagster._check as check
from dagster import resource
from dagster._core.log_manager import DagsterLogManager

from .types import SparkOpError
from .utils import construct_spark_shell_command


class SparkResource:
    def __init__(self, logger):
        self.logger = check.inst_param(logger, "logger", DagsterLogManager)

    def run_spark_job(self, config, main_class):
        check.dict_param(config, "config")
        check.str_param(main_class, "main_class")

        # Extract parameters from config
        (
            master_url,
            deploy_mode,
            application_jar,
            spark_conf,
            application_arguments,
            spark_home,
        ) = [
            config.get(k)
            for k in (
                "master_url",
                "deploy_mode",
                "application_jar",
                "spark_conf",
                "application_arguments",
                "spark_home",
            )
        ]

        if not os.path.exists(application_jar):
            raise SparkOpError(
                (
                    "Application jar {} does not exist. A valid jar must be "
                    "built before running this op.".format(application_jar)
                )
            )

        spark_shell_cmd = construct_spark_shell_command(
            application_jar=application_jar,
            main_class=main_class,
            master_url=master_url,
            spark_conf=spark_conf,
            deploy_mode=deploy_mode,
            application_arguments=application_arguments,
            spark_home=spark_home,
        )
        self.logger.info("Running spark-submit: " + " ".join(spark_shell_cmd))

        retcode = subprocess.call(" ".join(spark_shell_cmd), shell=True)

        if retcode != 0:
            raise SparkOpError("Spark job failed. Please consult your logs.")


@resource
def spark_resource(context):
    return SparkResource(context.log)
