'''A fully fleshed out demo dagster repository with many configurable options.'''

import itertools

from dagster import (
    check,
    Field,
    InputDefinition,
    OutputDefinition,
    Result,
    Selector,
    SolidDefinition,
)
from dagster import DagsterUserCodeExecutionError
from dagster.core.types.runtime import Stringish

from .configs import define_local_spark_config
from .configs_spark import parse_spark_config
from .utils import run_spark_subprocess


class SparkSolidError(DagsterUserCodeExecutionError):
    pass


class SparkResult(Stringish):
    description = 'A successful Spark job run'

    def __init__(self):
        super(SparkResult, self).__init__(description=SparkResult.description)


def define_local_spark_transform_fn(context, _):
    '''Define local Spark execution.

    This function defines how we'll execute the Spark job in the local deployment configuration.
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
    ) = [
        context.solid_config.get('local').get(k)
        for k in (
            'main_class',
            'master_url',
            'deploy_mode',
            'application_jar',
            'spark_conf',
            'application_arguments',
            'spark_home',
        )
    ]

    check.not_none_param(
        spark_home,
        'No spark home set. You must either provide spark_home or set $SPARK_HOME in your '
        'environment',
    )

    deploy_mode = ['--deploy-mode', '{}'.format(deploy_mode)] if deploy_mode else []

    spark_shell_cmd = (
        ['{}/bin/spark-submit'.format(spark_home), '--class', main_class, '--master', master_url]
        + deploy_mode
        + parse_spark_config(spark_conf)
        + [application_jar]
        + ([application_arguments] if application_arguments else [])
    )
    system_transform_context = context.get_system_context()
    system_transform_context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))

    retcode = run_spark_subprocess(spark_shell_cmd, system_transform_context.log)

    if retcode != 0:
        raise SparkSolidError('Spark job failed')

    yield Result('Spark job execution complete - success!')


def define_spark_solid(name, description=None, inputs=None, outputs=None):
    check.str_param(name, 'name')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)

    config_field = Field(Selector({'local': define_local_spark_config()}))

    description = (
        description or 'This solid is a generic representation of a parameterized Spark job.'
    )

    def transform_fn(context, _):
        if context.solid_config.get('local'):
            return define_local_spark_transform_fn(context, _)
        else:
            raise SparkSolidError('Invalid Spark configuration mode! Must be one of: (local)')

    return SolidDefinition(
        name=name,
        description=description,
        inputs=inputs,
        transform_fn=transform_fn,
        outputs=[OutputDefinition(SparkResult, description=SparkResult.description)],
        config_field=config_field,
    )
