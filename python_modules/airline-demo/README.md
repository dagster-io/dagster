This repository uses [git-lfs](https://git-lfs.github.com/).

### Running on AWS
The pipelines defined in this repository can run against a local Spark cluster
and Postgres instance, or they can run against a Redshift cluster and Spark
running on Amazon EMR.

We manage AWS resources with [pulumi](https://github.com/pulumi/pulumi).
First, install the pulumi CLI:

    brew install pulumi

Pulumi resources are divided by "project", in `pulumi/hosted_zone` and `pulumi/demo_resources`. The `hosted_zone` project configures Amazon Route53
to serve DNS for `dagster.io`, and shouldn't require much attention. To spin
resources up for a demo run, use the `demo_resources` project.

First, make sure you have the requirements. (You'll need to have already
installed TypeScript.)

    cd pulumi/demo_resources
    npm install

Then, you can bring up resources by running:

    pulumi up

This will take between 4 and 5 minutes.

To destroy resources, run:

    pulumi destroy

You can expect this to take

### TODOs

- Wire ingest pipeline up to Redshift
- Add config option for local ingestion (Postgres)
- Add config option for Spark running on EMR cluster
- Add S3 bucket for data sources
- Add solid to download from S3
- Wire up unzip file solid
- Wire up Spark join
- Write sql_solid
  