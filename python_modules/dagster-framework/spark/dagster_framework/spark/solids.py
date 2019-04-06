import os

from dagster import (
    check,
    Bool,
    InputDefinition,
    List,
    OutputDefinition,
    Path,
    Result,
    SolidDefinition,
)


from .configs import define_spark_config
from .types import SparkSolidError, SparkSolidOutputModeSuccess, SparkSolidOutputModePaths
from .utils import run_spark_subprocess, parse_spark_config


class SparkSolidDefinition(SolidDefinition):
    '''This solid is a generic representation of a parameterized Spark job.
    '''

    def __init__(self, name, description=None):
        name = check.str_param(name, 'name')
        description = check.opt_str_param(
            description,
            'description',
            'This solid is a generic representation of a parameterized Spark job.',
        )

        def _spark_transform_fn(context, _):
            '''Define Spark execution.

            This function defines how we'll execute the Spark job and invokes spark-submit.
            '''

            # Extract parameters from config
            (
                main_class,
                master_url,
                deploy_mode,
                application_jar,
                spark_conf,
                application_arguments,
                spark_home,
                spark_outputs,
                solid_output_mode,
            ) = [
                context.solid_config.get(k)
                for k in (
                    'main_class',
                    'master_url',
                    'deploy_mode',
                    'application_jar',
                    'spark_conf',
                    'application_arguments',
                    'spark_home',
                    'spark_outputs',
                    'solid_output_mode',
                )
            ]

            if not os.path.exists(application_jar):
                raise SparkSolidError(
                    (
                        'Application jar {} does not exist. A valid jar must be '
                        'built before running this solid.'.format(application_jar)
                    )
                )

            if spark_home is None:
                raise SparkSolidError(
                    (
                        'No spark home set. You must either pass spark_home in config or '
                        'set $SPARK_HOME in your environment (got None).'
                    )
                )

            deploy_mode = ['--deploy-mode', '{}'.format(deploy_mode)] if deploy_mode else []

            spark_shell_cmd = (
                [
                    '{}/bin/spark-submit'.format(spark_home),
                    '--class',
                    main_class,
                    '--master',
                    master_url,
                ]
                + deploy_mode
                + parse_spark_config(spark_conf)
                + [application_jar]
                + ([application_arguments] if application_arguments else [])
            )
            context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))
            retcode = run_spark_subprocess(spark_shell_cmd, context.log)

            if retcode != 0:
                raise SparkSolidError('Spark job failed. Please consult your logs.')

            if solid_output_mode == SparkSolidOutputModeSuccess.python_value:
                yield Result(True, SparkSolidOutputModeSuccess.python_value)
            elif solid_output_mode == SparkSolidOutputModePaths.python_value:
                yield Result(spark_outputs, SparkSolidOutputModePaths.python_value)
            else:
                raise SparkSolidError('should not reach')

        super(SparkSolidDefinition, self).__init__(
            name=name,
            description=description,
            inputs=[InputDefinition('spark_inputs', List(Path))],
            outputs=[
                OutputDefinition(
                    dagster_type=Bool,
                    name=SparkSolidOutputModeSuccess.python_value,
                    is_optional=True,
                ),
                OutputDefinition(
                    dagster_type=List(Path),
                    name=SparkSolidOutputModePaths.python_value,
                    is_optional=True,
                ),
            ],
            transform_fn=_spark_transform_fn,
            config_field=define_spark_config(),
        )
