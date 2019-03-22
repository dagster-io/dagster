'''A fully fleshed out demo dagster repository with many configurable options.'''

from dagster import solid, Field, Dict, String

from .types import SparkDeployTarget, SparkDeployTargetLocal, SparkDeployMode, SparkDeployModeClient


@solid(
    name='SparkJobSolid',
    description='''
    This solid is a generic representation of a parameterized Spark job.
    ''',
    inputs=[],
    outputs=[],
    config_field=Field(
        Dict(
            # See the Spark documentation for reference:
            # https://spark.apache.org/docs/latest/submitting-applications.html
            fields={
                'deploy_target': Field(
                    SparkDeployTarget,
                    description='''This solid supports several deploy targets for your Spark 
                    application: Local Spark (default), a remote Spark master, AWS EMR, and GCP 
                    Dataproc.''',
                    default_value=SparkDeployTargetLocal,
                    is_optional=False,
                ),
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
                    SparkDeployMode,
                    description='''Whether to deploy your driver on the worker nodes (cluster) or 
                    locally as an external client (client) (default: client). A common deployment 
                    strategy is to submit your application from a gateway machine that is physically
                    co-located with your worker machines (e.g. Master node in a standalone EC2
                    cluster). In this setup, client mode is appropriate. In client mode, the driver
                    is launched directly within the spark-submit process which acts as a client to 
                    the cluster. The input and output of the application is attached to the console.
                    Thus, this mode is especially suitable for applications that involve the REPL 
                    (e.g. Spark shell).''',
                    default_value=SparkDeployModeClient,
                    is_optional=False,
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
                ),
                'application_arguments': Field(
                    Dict(fields={}),
                    description='Arguments passed to the main method of your main class, if any',
                ),
            }
        )
    ),
)
def SparkJobSolid(context):
    main_class = context.solid_config['main_class']
    master_url = context.solid_config['master_url']
    deploy_mode = context.solid_config['deploy_mode']
    application_jar = context.solid_config['application_jar']
    conf = context.solid_config['conf']
    application_arguments = context.solid_config['arguments']

    shell_cmd = """
    {spark_home}/bin/spark-submit \\
  --class {main_class} \\
  --master {master_url} \\
  --deploy-mode {deploy_mode} \\
  {conf} \\ 
  {application_jar} \\
  {application_arguments}
""".strip().format(
        main_class=main_class,
        master_url=master_url,
        deploy_mode=deploy_mode,
        conf=conf,
        application_jar=application_jar,
        application_arguments=application_arguments,
    )

