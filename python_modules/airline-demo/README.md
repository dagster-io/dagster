# Airline demo

This repository is intended as a fleshed-out demo of Dagster's capabilities. It defines three
realistic data pipelines corresponding to stereotyped download, ingest, and analysis phases of
typical data science workflows, using real-world airline data. Although the view of the pipelines
provided by the Dagster tooling is unified, in typical practice we expect that each pipeline is
likely to be the responsibility of individuals with more or less clearly distinguished roles.

Use the airline demo to familiarize yourself with the features of the Dagster tooling in a more
fleshed-out context than the introductory tutorial, and as a reference when building your own
first production pipelines in the system. Comments and suggestions are enthusiastically encouraged!

## Getting started

To run the airline demo pipelines locally, you'll need

- An Internet connection
- AWS credentials in the ordinary [boto3 credential chain](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html)
- An [Apache Spark](https://spark.apache.org/downloads.html) install
- A running Postgres database available at `postgresql://test:test@127.0.0.1:5432/test`. (A
  docker-compose file is provided in this repo; run `docker-compose up` from the root of the
  airline demo.)

Use pip to install the demo's Python requirements:

    pip install -e .

Then just run dagit from the root of the repo:

    dagit


## Pipelines and config

The demo defines a single repository with three pipelines, in `airline_demo/pipelines.py`:

- **airline_demo_download_pipeline** grabs data archives from S3 and unzips them.
- **airline_demo_ingest_pipeline** reads the raw data into Spark, performs some typical
  manipulations on the data, and then loads tables into a data warehouse.
- **airline_demo_warehouse_pipeline** performs typical in-warehouse analysis and manipulations
  using SQL, and then generates and archives analysis artifacts and plots using Jupyter notebooks.

Sample configuration files for running the demo pipelines are provided under `environments/`. To run
the pipelines locally, use the configuration files that begin with the prefix `local_`.

To avoid unnecessary duplication, the config that is common to all of the pipelines is factored
out into `local_base.yml` file. Recall that when running a pipeline using `dagster pipeline execute`
you can pass more than one yaml file using the `-e` flag, and these will be combined.

### Running tests

You won't want to suppress test output if you want to see loglines from dagster:

    pytest -s

We use [pytest marks](https://docs.pytest.org/en/latest/example/markers.html#mark-examples) to
identify useful subsets of tests. For instance, to run only those tests that do not require a
running Spark cluster, you can run:

    pytest -m "not spark"

## The download pipeline

![Download pipeline](img/download_pipeline.png)

The `airline_demo_download_pipeline` models the first stage of most data science workflows, in
which raw data is consumed from a variety of sources. 

For demo purposes, we've put our source files in a publicly-readable S3 repository. In practice,
these might be files in S3 or other cloud storage systems; publicly available datasets downloaded
over http; or batch files in an SFTP drop.

### Running the pipeline locally with test config

If you want to start by running this pipeline, try the config fragment in
`environments/local_test_download.yml`. The first time you run this pipeline, you'll likely see a
bunch of log lines in the terminal running dagit as Spark dependencies are resolved.

This config fragment points to cut-down versions of the original data files on S3. It can be good
practice to maintain similar test sets so that you can run fast versions of your data pipelines
locally or in test environments. While there are many faults that will not be caught by using small
cut-down or synthetic data sets -- for example, data issues that may only appear in production data
or at scale -- this practice will allow you to verify the integrity of your pipeline construction
and to catch at least some semantic issues.

![Download pipeline run](img/download_pipeline_run.png)

### Defining a pipeline with library solids

Let's start by looking at the pipeline definition (in `airline_demo/pipelines.py`):

    def define_airline_demo_download_pipeline():
        solids = [download_from_s3, unzip_file]
        dependencies = {
            SolidInstance('download_from_s3', alias='download_archives'): {},
            SolidInstance('unzip_file', alias='unzip_archives'): {
                'archive_paths': DependencyDefinition('download_archives')
            },
            SolidInstance('download_from_s3', alias='download_q2_sfo_weather'): {},
        }

        return PipelineDefinition(
            name='airline_demo_download_pipeline',
            context_definitions=CONTEXT_DEFINITIONS,
            solids=solids,
            dependencies=dependencies,
        )

The first thing to note is that we're relying on `SolidInstance` to build our pipeline by defining
aliased instances (`download_archives`, `unzip_archives`, `download_q2_sfo_weather`) of
reusable library solids (`download_from_s3`, `unzip_file`).

In general, you won't want every data science user in your organization to have to roll their own
implementation of common functionality like downloading and unzipping files. Instead, you'll want to
abstract common functionality into reusable solids, separating task-specific parameters out into
declarative config, and building up a library of building blocks for new data pipelines.

### Implementing a library solid with List-typed inputs and outputs

Let's take a look at how one of these library solids is defined:

    @solid(
        name='download_from_s3',
        config_field=Field(
            List(
                Dict(
                    fields={
                        # Probably want to make the region configurable too
                        'bucket': Field(
                            String, description='The S3 bucket in which to look for the key.'
                        ),
                        'key': Field(String, description='The key to download.'),
                        'skip_if_present': Field(
                            Bool,
                            description=(
                                'If True, and a file already exists at the path described by the '
                                'target_path config value, if present, or the key, then the solid '
                                'will no-op.'
                            ),
                            default_value=False,
                            is_optional=True,
                        ),
                        'target_path': Field(
                            Path,
                            description=(
                                'If present, specifies the path at which to download the object.'
                            ),
                            is_optional=True,
                        ),
                    }
                )
            )
        ),
        description='Downloads an object from S3.',
        outputs=[
            OutputDefinition(List(FileExistsAtPath), description='The path to the downloaded object.')
        ],
    )
    def download_from_s3(context):
        '''Download an object from s3.

        Args:
            info (ExpectationExecutionInfo): Must expose a boto3 S3 client as its `s3` resource.

        Returns:
            str:
                The path to the downloaded object.
        '''
        results = []
        for file_ in context.solid_config:
            bucket = file_['bucket']
            key = file_['key']
            target_path = file_.get('target_path') or key

            if target_path is None:
                target_path = context.resources.tempfile.tempfile().name

            if file_['skip_if_present'] and safe_isfile(target_path):
                context.log.info(
                    'Skipping download, file already present at {target_path}'.format(
                        target_path=target_path
                    )
                )
            else:
                if os.path.dirname(target_path):
                    mkdir_p(os.path.dirname(target_path))

                context.resources.s3.download_file(bucket, key, target_path)
            results.append(target_path)
        return results

There's a lot to unpack here, but let's start with the config field on the solid. We define this
solid using a `List` type so that it can download an arbitrary number of files in a single step.
This lets us avoid a typical pattern in DAG and workflow definitions where a single vertical DAG
fragment is repeated horizontally N times, once for each data source being processed. You will
probably be familiar with DAGs that look like the following:

![Download pipeline alternate](img/download_pipeline_alternate.png)

By using a List type, we can add or remove new data sources by adjusting config, rather than by
adding or removing DAG fragment definitions. Of course, there may be cases in which a more explicit
graph is preferable -- for example, if the same operations are being executed on two sets of inputs,
but the downstream dependencies are independent. Actually, you can see an example of this in this
very pipeline -- the output of `download_q2_sfo_weather` does not need to be unzipped, and so we've
defined a separate alias (still using the same library solid -- and underlying List type -- for
maximum flexibility).

### Strongly typed config and outputs

Each entry in the config list for our solid specifies everything we need to know to download a
file from S3 (at least in our toy example). In YAML, an entry in the config looks like this:

    - bucket: dagster-airline-demo-source-data
      key: test/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip
      skip_if_present: false
      target_path: source_data/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_4.zip

Because each of these values is strongly typed, we'll get rich error information in the dagit
config editor (or when running pipelines from the command line) when a config value is incorrectly
specified.

![Download pipeline bad config](img/download_pipeline_bad_config.png)

While this may seem like a mere convenience, in production contexts it can dramatically reduce
avoidable errors. Consider boto3's [S3.Client.put_object](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.put_object)
method, which has 28 parameters, many restricted in obscure ways (for example,
`ServerSideEncryption` must be one of `'AES256'|'aws:kms'`). Strongly typed config schemas can catch
any error of this type.

By setting the `description` on each of our config members, we also get easily navigable
documentation in dagit. Users of library solids no longer need to investigate implementations in
order to understand what values are required, or what they do -- enabling more confident reuse.

![Download pipeline config docs](img/download_pipeline_config_docs.png)

### Custom types

Note that the output of this solid is also a List -- in this case, a `List(FileExistsAtPath)`. We've
defined a custom output type to illustrate the richness of the Dagster type system:

    from dagster.core.types.runtime import Stringish
    from dagster.utils import safe_isfile

    class FileExistsAtPath(Stringish):
        def __init__(self):
            super(FileExistsAtPath, self).__init__(description='A path at which a file actually exists')

        def coerce_runtime_value(self, value):
            value = super(FileExistsAtPath, self).coerce_runtime_value(value)
            return self.throw_if_false(safe_isfile, value)

By overriding `coerce_runtime_value` to check if a file actually exists at the specified path, we
can lever the type system to make runtime guarantees about the integrity of our pipeline.

### Robust solids for development workflows

Notice the `skip_if_present` key in the config for both `download_from_s3` and `unzip_file`. We've
included this to illustrate how you can introduce knobs into your solids that make moving between
development, test, and production environments and workflows easier.

In production, you may have pipelines that grab large files from batch processes or filedrops, and
that may take minutes or hours to execute. But in development, you probably won't want to download
large data every time you make a small tweak to a pipeline. Practitioners often find themselves
writing special-case wrappers to handle their local workflows -- for instance, to download files
only if they are not already present on the local file system.

Here, we've moved that logic into the body of the solid itself. Because we can turn this feature on
and off with config, we don't need to write ad hoc tooling to support local workflows. Instead, the
same pipeline can run locally as runs in production. This makes it easier both to develop locally
with a short feedback cycle and to write and run tests against pipeline code.

### Running on production data

Don't worry, we've got plenty of big(gish) data to run through this pipeline. Instead of the
`local_fast_download.yml` config fragment, use `local_full_download.yml` -- but be prepared to wait!


## The ingest pipeline

![Download pipeline](img/download_pipeline.png)

The `airline_demo_download_pipeline` models the first stage of most data science workflows, in
which raw data is consumed from a variety of sources. 

For demo purposes, we've put our source files in a publicly-readable S3 repository. In practice,
these might be files in S3 or other cloud storage systems; publicly available datasets downloaded
over http; or batch files in an SFTP drop.


<!--
FIXME need to actually describe how to run this pipeline against AWS

### Orchestrating AWS resources
The pipelines defined in this repository can run against a local Spark cluster
and Postgres instance, or they can run against a Redshift cluster and Spark
running on Amazon EMR.

We manage AWS resources with [pulumi](https://github.com/pulumi/pulumi).
First, install the pulumi CLI:

    brew install pulumi

Pulumi resources are divided by "project". To spin resources up for a demo run,
use the `demo_resources` project.

First, make sure you have the requirements. (You'll need to have already
installed TypeScript.)

    cd pulumi/demo_resources
    npm install

Then, you can bring up resources by running:

    pulumi up

This will take between 4 and 5 minutes.

To destroy resources, run:

    pulumi destroy

<small>
*Warning*: Currently we are unable to cleanly tear down the VPC using pulumi
because of dependency errors like the following:

    error: Plan apply failed: deleting urn:pulumi:demo_resources-dev::demo_resources::aws-infra:network:Network$aws:ec2/vpc:Vpc::airline_demo_vpc: DependencyViolation: The vpc 'vpc-01a7f7c286196cdc0' has dependencies and cannot be deleted.
        status code: 400, request id: 03a586f3-e17e-41e2-b5fd-c4275226df30

It's unclear whether this is an issue with pulumi/aws-infra or something else,
maybe the autogenerated EMR slave and master security groups (? -- but if so,
see https://github.com/pulumi/pulumi/issues/1691 -- or, if this is in fact an issue
with the underlying terraform provider, see https://github.com/terraform-providers/terraform-provider-aws/issues/3465,
and many other issues suggesting the EMR resource in the AWS provider is not
fully mature). There is no good way to find out *which* dependency is causing
this error (generated in the AWS CLI), and no way to force delete dependencies
from the command line (See: https://github.com/aws/aws-cli/issues/1721,
https://forums.aws.amazon.com/thread.jspa?threadID=223412).

Right now the workaround is to wait for a timeout (about 15 minutes), then
manually delete the VPC from the console, which will force-delete dependencies.
</small>

### Issues with general availability
- Right now the pulumi spec, as well as the sample config, expect that you will
be able to orchestrate a Redshift cluster at `db.dagster.io` and an EMR cluster
at `spark.dagster.io`. If you are running this demo and you do not control
`dagster.io`, you will need to edit both the pulumi project and the config to
point these at DNS you do control.

-->

### TODOs

- Flesh out unit tests for solids
- Write ephemeral EMR cluster resource
- Add expectations
- Maybe implement templated SQL handling
- Add sub-DAG tests
