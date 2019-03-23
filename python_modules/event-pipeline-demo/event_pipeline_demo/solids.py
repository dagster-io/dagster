'''A fully fleshed out demo dagster repository with many configurable options.'''

import os
import re
import subprocess
import itertools

from six.moves import queue
from threading import Thread

from dagster import (
    as_dagster_type,
    check,
    ConfigType,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    String,
)
from dagster.core.errors import DagsterError
from dagster.core.types.runtime import Stringish

from .types import SparkDeployTarget, SparkDeployTargetLocal, SparkDeployMode, SparkDeployModeClient


def run_spark_subprocess(cmd, logger):
    # See: https://bit.ly/2OpksJC for source of this pattern

    # Spark sometimes logs in log4j format. In those cases, we detect and parse
    log4j_regex = r'^(\d{4}\-\d{2}\-\d{2} \d{2}:\d{2}:\d{2}) ([A-Z]{3,5})(.*?)$'

    def reader(pipe, pipe_name, p, msg_queue):
        try:
            with pipe:
                while p.poll() is None:
                    for line in pipe.readlines():
                        match = re.match(log4j_regex, line)
                        if match:
                            line = match.groups()[2]
                        msg_queue.put((pipe_name, line))
        finally:
            msg_queue.put(None)

    p = subprocess.Popen(
        ' '.join(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        universal_newlines=True,
        shell=True,
    )
    q = queue.Queue()
    Thread(target=reader, args=[p.stdout, 'stdout', p, q]).start()
    Thread(target=reader, args=[p.stderr, 'stderr', p, q]).start()
    for _ in range(2):  # There will be two None sentinels, one for each stream
        for pipe_name, line in iter(q.get, None):
            if pipe_name == 'stdout':
                logger.info(line)
            elif pipe_name == 'stderr':
                logger.error(line)

    p.wait()
    return p.returncode


class SparkSolidError(DagsterError):
    pass


class MyDict(ConfigType):
    pass


class SparkResult(Stringish):
    description = 'A successful Spark job run'

    def __init__(self):
        super(SparkResult, self).__init__(description=SparkResult.description)


def SparkSolid(name, description=None, inputs=None, outputs=None):
    check.str_param(name, 'name')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)
    config_field = Field(
        Dict(
            # See the Spark documentation for reference:
            # https://spark.apache.org/docs/latest/submitting-applications.html
            fields={
                # 'deploy_target': Field(
                #     SparkDeployTarget,
                #     description='''This solid supports several deploy targets for your Spark
                #     application: Local Spark (default), a remote Spark master, AWS EMR, and GCP
                #     Dataproc.''',
                #     default_value=SparkDeployTargetLocal,
                #     is_optional=False,
                # ),
                'main_class': Field(
                    String,
                    description='''The entry point for your application (e.g. 
                    org.apache.spark.examples.SparkPi)''',
                    is_optional=False,
                ),
                'master_url': Field(
                    String,
                    description='The master URL for the cluster (e.g. spark://23.195.26.187:7077)',
                    is_optional=False,
                ),
                'deploy_mode': Field(
                    String,
                    description='''Whether to deploy your driver on the worker nodes (cluster) or 
                    locally as an external client (client) (default: client). A common deployment 
                    strategy is to submit your application from a gateway machine that is physically
                    co-located with your worker machines (e.g. Master node in a standalone EC2
                    cluster). In this setup, client mode is appropriate. In client mode, the driver
                    is launched directly within the spark-submit process which acts as a client to 
                    the cluster. The input and output of the application is attached to the console.
                    Thus, this mode is especially suitable for applications that involve the REPL 
                    (e.g. Spark shell).''',
                    is_optional=True,
                ),
                'application_jar': Field(
                    String,
                    description='''Path to a bundled jar including your application and all 
                    dependencies. The URL must be globally visible inside of your cluster, for 
                    instance, an hdfs:// path or a file:// path that is present on all nodes.''',
                    is_optional=False,
                ),
                'conf': Field(
                    Dict(fields={}),
                    description='''Arbitrary Spark configuration property in key=value format. For 
                    values that contain spaces wrap “key=value” in quotes.''',
                    is_optional=True,
                ),
                'application_arguments': Field(
                    String,
                    description='Arguments passed to the main method of your main class, if any',
                    is_optional=True,
                ),
                'spark_home': Field(
                    String,
                    description='The path to your spark installation. Defaults to $SPARK_HOME',
                    is_optional=True,
                    default_value=os.environ.get('SPARK_HOME'),
                ),
            }
        )
    )
    description = (
        description or 'This solid is a generic representation of a parameterized Spark job.'
    )

    def transform_fn(context, _):
        check.not_none_param(
            context.solid_config.get('spark_home'),
            'No spark home set. You must either provide spark_home or set $SPARK_HOME in your'
            'environment.',
        )

        # Extract parameters from config
        (
            main_class,
            master_url,
            deploy_mode,
            application_jar,
            conf,
            application_arguments,
            spark_home,
        ) = [
            context.solid_config.get(k)
            for k in (
                'main_class',
                'master_url',
                'deploy_mode',
                'application_jar',
                'conf',
                'application_arguments',
                'spark_home',
            )
        ]

        deploy_mode = ['--deploy-mode', '{}'.format(deploy_mode)] if deploy_mode else []

        # For each key-value pair in spark conf, we need to pass to CLI in format:
        # --conf "key=value"
        spark_cli_conf = (
            list(
                itertools.chain.from_iterable(
                    [('--conf', '{}={}'.format(c.key, c.value)) for c in conf]
                )
            )
            if conf
            else []
        )

        spark_shell_cmd = (
            [
                '{}/bin/spark-submit'.format(spark_home),
                '--class',
                main_class,
                '--master',
                master_url,
            ]
            + deploy_mode
            + spark_cli_conf
            + [application_jar]
            + ([application_arguments] if application_arguments else [])
        )
        system_transform_context = context.get_system_context()

        print(spark_shell_cmd)
        system_transform_context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))

        retcode = run_spark_subprocess(spark_shell_cmd, system_transform_context.log)

        if retcode != 0:
            raise SparkSolidError('Spark job failed')

        system_transform_context.log.debug(
            'Spark job execution complete for {name}'.format(name=name)
        )

        yield Result(value='_SUCCESS', output_name='result')

    return SolidDefinition(
        name=name,
        description=description,
        inputs=inputs,
        transform_fn=transform_fn,
        outputs=[OutputDefinition(SparkResult, description=SparkResult.description)],
        config_field=config_field,
    )

