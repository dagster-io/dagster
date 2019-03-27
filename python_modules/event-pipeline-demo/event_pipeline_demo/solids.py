from dagster import check, InputDefinition, OutputDefinition, Result, SolidDefinition
from dagster import DagsterUserCodeExecutionError


from .configs import define_spark_config, parse_spark_config
from .utils import run_spark_subprocess


class SparkSolidError(DagsterUserCodeExecutionError):
    pass


def define_spark_transform_fn(context, inputs):
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
        spark_outputs,
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
    system_context = context.get_system_context()
    system_context.log.info("Running spark-submit: " + ' '.join(spark_shell_cmd))
    retcode = run_spark_subprocess(spark_shell_cmd, system_context.log)

    if retcode != 0:
        raise SparkSolidError('Spark job failed')

    for output_def in system_context.solid_def.output_defs:
        yield Result(spark_outputs, output_def.name)


def define_spark_solid(name, inputs, outputs, description=None):
    check.str_param(name, 'name')
    inputs = check.opt_list_param(inputs, 'input_defs', of_type=InputDefinition)
    outputs = check.opt_list_param(outputs, 'output_defs', of_type=OutputDefinition)

    description = (
        description or 'This solid is a generic representation of a parameterized Spark job.'
    )

    return SolidDefinition(
        name=name,
        description=description,
        transform_fn=define_spark_transform_fn,
        inputs=inputs,
        outputs=outputs,
        config_field=define_spark_config(),
    )
