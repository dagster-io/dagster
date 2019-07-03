import functools
import os

from dagster import check, InputDefinition, List, OutputDefinition, Path, Output, SolidDefinition


from .configs import define_spark_config
from .types import SparkSolidError
from .utils import run_spark_subprocess, parse_spark_config


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


def step_metadata_fn(environment_config, solid_name, main_class):
    return {
        'spark_submit_command': ' '.join(
            create_spark_shell_cmd(environment_config.solids[solid_name].config, main_class)
        )
    }


class SparkSolidDefinition(SolidDefinition):
    '''This solid is a generic representation of a parameterized Spark job.

    Parameters:
    name (str): The name of this Spark solid
    main_class (str): The entry point for your application (e.g. org.apache.spark.examples.SparkPi)

    '''

    def __init__(self, name, main_class, description=None):
        name = check.str_param(name, 'name')
        main_class = check.str_param(main_class, 'main_class')
        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Spark job.',
        )

        def _spark_compute_fn(context, _):
            '''Define Spark execution.

            This function defines how we'll execute the Spark job and invokes spark-submit.
            '''

            spark_shell_cmd = create_spark_shell_cmd(context.solid_config, main_class)

            context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))
            retcode = run_spark_subprocess(spark_shell_cmd, context.log)

            if retcode != 0:
                raise SparkSolidError('Spark job failed. Please consult your logs.')

            yield Output(context.solid_config.get('spark_outputs'), 'paths')

        super(SparkSolidDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=[InputDefinition('spark_inputs', List[Path])],
            output_defs=[OutputDefinition(dagster_type=List[Path], name='paths')],
            compute_fn=_spark_compute_fn,
            config_field=define_spark_config(),
            metadata={'kind': 'spark', 'main_class': main_class},
            step_metadata_fn=functools.partial(
                step_metadata_fn, solid_name=name, main_class=main_class
            ),
        )
