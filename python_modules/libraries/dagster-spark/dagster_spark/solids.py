import os
import subprocess

from dagster import (
    InputDefinition,
    List,
    Nothing,
    Output,
    OutputDefinition,
    Path,
    SolidDefinition,
    check,
    solid,
)

from .configs import define_spark_config
from .types import SparkSolidError
from .utils import parse_spark_config


def create_spark_shell_cmd(solid_config, main_class):
    # Extract parameters from config
    (master_url, deploy_mode, application_jar, spark_conf, application_arguments, spark_home) = [
        solid_config.get(k)
        for k in (
            'master_url',
            'deploy_mode',
            'application_jar',
            'spark_conf',
            'application_arguments',
            'spark_home',
        )
    ]

    # Let the user use env vars in the jar path
    application_jar = os.path.expandvars(application_jar)

    if not os.path.exists(application_jar):
        raise SparkSolidError(
            (
                'Application jar {} does not exist. A valid jar must be '
                'built before running this solid.'.format(application_jar)
            )
        )

    spark_home = spark_home if spark_home else os.environ.get('SPARK_HOME')

    if spark_home is None:
        raise SparkSolidError(
            (
                'No spark home set. You must either pass spark_home in config or '
                'set $SPARK_HOME in your environment (got None).'
            )
        )

    deploy_mode = ['--deploy-mode', '{}'.format(deploy_mode)] if deploy_mode else []

    spark_shell_cmd = (
        ['{}/bin/spark-submit'.format(spark_home), '--class', main_class, '--master', master_url]
        + deploy_mode
        + parse_spark_config(spark_conf)
        + [application_jar]
        + ([application_arguments] if application_arguments else [])
    )
    return spark_shell_cmd


class SparkSolidDefinition(SolidDefinition):
    '''This solid is a generic representation of a parameterized Spark job.

    Parameters:
    name (str): The name of this Spark solid
    main_class (str): The entry point for your application (e.g. org.apache.spark.examples.SparkPi)

    '''

    def __init__(self, name, main_class, spark_outputs=None, description=None):
        name = check.str_param(name, 'name')
        main_class = check.str_param(main_class, 'main_class')
        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Spark job.',
        )
        spark_outputs = check.opt_list_param(spark_outputs, 'spark_outputs', of_type=str)

        def _spark_compute_fn(context, _):
            '''Define Spark execution.

            This function defines how we'll execute the Spark job and invokes spark-submit.
            '''

            spark_shell_cmd = create_spark_shell_cmd(context.solid_config, main_class)

            context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))
            retcode = subprocess.call(' '.join(spark_shell_cmd), shell=True)

            if retcode != 0:
                raise SparkSolidError('Spark job failed. Please consult your logs.')

            yield Output(spark_outputs, 'paths')

        super(SparkSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition('spark_inputs', List[Path])],
            output_defs=[OutputDefinition(dagster_type=List[Path], name='paths')],
            compute_fn=_spark_compute_fn,
            config=define_spark_config(),
            tags={'kind': 'spark', 'main_class': main_class},
        )


def create_spark_solid(name, main_class, description=None):
    check.str_param(name, 'name')
    check.str_param(main_class, 'main_class')
    check.opt_str_param(description, 'description', 'A parameterized Spark job.')

    @solid(
        name=name,
        description=description,
        config=define_spark_config(),
        input_defs=[InputDefinition('start', Nothing)],
        output_defs=[OutputDefinition(Nothing)],
        tags={'kind': 'spark', 'main_class': main_class},
        required_resource_keys={'spark'},
    )
    def spark_solid(context):  # pylint: disable=unused-argument
        context.resources.spark.run_spark_job(context.solid_config, main_class)

    return spark_solid
