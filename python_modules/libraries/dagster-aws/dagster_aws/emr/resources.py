import os

import boto3
import six
from dagster_aws.utils.mrjob.log4j import parse_hadoop_log4j_records
from dagster_pyspark import PySparkResourceDefinition
from dagster_spark.configs_spark import spark_config
from dagster_spark.utils import flatten_dict, format_for_cli

from dagster import Field, check, resource
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.seven import get_system_temp_directory

from .emr import EmrJobRunner
from .utils import build_main_file, build_pyspark_zip

# On EMR, Spark is installed here
EMR_SPARK_HOME = '/usr/lib/spark/'


class EmrPySparkResource(PySparkResourceDefinition):
    def __init__(self, config):
        self.config = config
        self.emr_job_runner = EmrJobRunner(region=self.config['region_name'])
        self.s3_client = boto3.client('s3', region_name=self.config['region_name'])

        # Construct the SparkSession
        super(EmrPySparkResource, self).__init__(self.config.get('spark_conf'))

    def get_compute_fn(self, fn, solid_name):
        '''Construct new compute function for EMR pyspark execution. In the scenario where we are
        running on a Dagster box, we will (1) sync the client code to an S3 staging bucket, and then
        (2) invoke execution via the EMR APIs.

        On EMR, we'll just return the original solid function body to kick off normal pyspark
        execution. Since that will be launched on the EMR master node with YARN, it will
        automatically use the EMR cluster for execution.
        '''

        if self.running_on_emr:
            return fn

        def new_compute_fn(context, *args, **kwargs):  # pylint: disable=unused-argument
            self._sync_code_to_s3(context, solid_name)
            step_defs = self._get_execute_steps(context, solid_name)
            step_ids = self.emr_job_runner.add_job_flow_steps(
                context, self.config['cluster_id'], step_defs
            )
            self.emr_job_runner.wait_for_steps_to_complete(
                context, self.config['cluster_id'], step_ids
            )
            if self.config['wait_for_logs']:
                stdout_log, stderr_log = self.emr_job_runner.retrieve_logs_for_step_id(
                    context, self.config['cluster_id'], step_ids[1]
                )
                # Since stderr is YARN / Hadoop Log4J output, parse and reformat those log lines for
                # Dagster's logging system.
                records = parse_hadoop_log4j_records(stderr_log)
                for record in records:
                    context.log._log(  # pylint: disable=protected-access
                        record.level, record.logger + ': ' + record.message, {}
                    )
                context.log.info(stdout_log)

        return new_compute_fn

    def _sync_code_to_s3(self, context, solid_name):
        '''Synchronize the pyspark code to an S3 staging bucket for use on EMR. Note that
        requirements are installed separately when a requirements.txt is provided.

        For the zip file, consider the following toy example:

        # Folder: my_pyspark_project/
        # a.py
        def foo():
            print(1)

        # b.py
        def bar():
            print(2)

        # main.py
        from a import foo
        from b import bar

        foo()
        bar()

        This will zip up `my_pyspark_project/` as `my_pyspark_project.zip`. Then, when running
        `spark-submit --py-files my_pyspark_project.zip main.py` on EMR this will print 1, 2.

        Note that we also dynamically construct main.py to support targeting execution of a single
        solid on EMR vs. the entire pipeline.
        '''
        run_id = context.run_id
        main_file = os.path.join(get_system_temp_directory(), '%s-main.py' % run_id)
        zip_file = os.path.join(get_system_temp_directory(), '%s-pyspark.zip' % run_id)

        try:
            build_main_file(
                main_file,
                mode_name=context.pipeline_run.mode,
                pipeline_file=self.config['pipeline_file'],
                solid_name=solid_name,
                environment_dict=context.environment_dict,
                pipeline_fn_name=self.config['pipeline_fn_name'],
            )

            build_pyspark_zip(
                zip_file=zip_file,
                path=os.path.dirname(os.path.abspath(self.config['pipeline_file'])),
            )

            self.s3_client.upload_file(
                zip_file, self.config['staging_bucket'], run_id + '/pyspark.zip'
            )
            self.s3_client.upload_file(
                main_file, self.config['staging_bucket'], run_id + '/main.py'
            )

        finally:
            if os.path.exists(main_file):
                os.unlink(main_file)
            if os.path.exists(zip_file):
                os.unlink(zip_file)

    def _get_execute_steps(self, context, solid_name):
        '''From the local Dagster instance, construct EMR steps that will kick off execution on a
        remote EMR cluster.
        '''
        action_on_failure = self.config['action_on_failure']
        staging_bucket = self.config['staging_bucket']

        run_id = context.run_id
        local_root = os.path.dirname(os.path.abspath(self.config['pipeline_file']))

        steps = []

        # Install Python dependencies if a requirements file exists
        requirements_file = self.config.get('requirements_file_path')
        if requirements_file and not os.path.exists(requirements_file):
            raise DagsterInvalidDefinitionError(
                'The requirements.txt file that was specified does not exist'
            )

        if not requirements_file:
            requirements_file = os.path.join(local_root, 'requirements.txt')

        if os.path.exists(requirements_file):
            with open(requirements_file, 'rb') as f:
                python_dependencies = six.ensure_str(f.read()).split('\n')
                steps.append(
                    EmrJobRunner.construct_step_dict_for_command(
                        'Install Dependencies',
                        ['sudo', 'python3', '-m', 'pip', 'install'] + python_dependencies,
                        action_on_failure=action_on_failure,
                    )
                )

        # Execute Solid via spark-submit
        conf = dict(flatten_dict(self.config.get('spark_conf')))
        conf['spark.app.name'] = conf.get('spark.app.name', solid_name)

        check.invariant(
            conf.get('spark.master', 'yarn') == 'yarn',
            desc='spark.master is configured as %s; cannot set Spark master on EMR to anything '
            'other than "yarn"' % conf.get('spark.master'),
        )

        command = (
            [
                EMR_SPARK_HOME + 'bin/spark-submit',
                '--master',
                'yarn',
                '--deploy-mode',
                conf.get('spark.submit.deployMode', 'client'),
            ]
            + format_for_cli(list(flatten_dict(conf)))
            + [
                '--py-files',
                's3://%s/%s/pyspark.zip' % (staging_bucket, run_id),
                's3://%s/%s/main.py' % (staging_bucket, run_id),
            ]
        )

        steps.append(
            EmrJobRunner.construct_step_dict_for_command(
                'Execute Solid %s' % solid_name, command, action_on_failure=action_on_failure
            )
        )
        return steps

    @property
    def running_on_emr(self):
        '''Detects whether we are running on the EMR cluster
        '''
        if os.path.exists('/mnt/var/lib/info/job-flow.json'):
            return True
        return False


@resource(
    {
        'pipeline_file': Field(str, description='Path to the file where the pipeline is defined'),
        'pipeline_fn_name': Field(str),
        'spark_config': spark_config(),
        'cluster_id': Field(str, description='Name of the job flow (cluster) on which to execute'),
        'region_name': Field(str),
        'action_on_failure': Field(str, is_required=False, default_value='CANCEL_AND_WAIT'),
        'staging_bucket': Field(
            str,
            is_required=True,
            description='S3 staging bucket to use for staging the produced main.py and zip file of'
            ' Python code',
        ),
        'requirements_file_path': Field(
            str,
            is_required=False,
            description='Path to a requirements.txt file; the current directory is searched if none'
            ' is specified.',
        ),
        'wait_for_logs': Field(
            bool,
            is_required=False,
            default_value=False,
            description='If set, the system will wait for EMR logs to appear on S3. Note that logs '
            'are copied every 5 minutes, so enabling this will add several minutes to the job '
            'runtime',
        ),
    }
)
def emr_pyspark_resource(init_context):
    emr_pyspark = EmrPySparkResource(init_context.resource_config)
    try:
        yield emr_pyspark
    finally:
        emr_pyspark.stop()
