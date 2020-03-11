.. _deployment-aws:

Deploying to AWS
----------------


Quick start with dagster-aws
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``dagster_aws`` package includes a CLI tool intended to help you get a demo Dagster
deployment up and running as quickly as possible.

**NOTE: The dagster-aws CLI is not intended to provide a secure configuration, and the instance
it sets up will be launched into an existing VPC and publicly accessible. In production settings,
you will want to launch Dagit into an appropriately configured VPC, using an appropriate security
group, etc.** We generally recommend that you use an infrastructure-as-code toolchain, such as
`Terraform <https://www.terraform.io/>`_ or `Pulumi <https://www.pulumi.com/>`_, to manage your
cloud deployments.

Ensure you have AWS credentials on your local machine, and that the `DAGSTER_HOME` environment
variable is set, and then run:

.. code-block:: shell

    pip install dagster dagit dagster-aws
    dagster-aws init

This script will walk you through the set up of an EC2 instance to host Dagit. You can also choose
to launch an RDS instance (Postgres) to host run and event log storage; if you do so, the remote
EC2 instance will automatically be configured to talk to RDS via an appropriate ``dagster.yaml``
file on the remote at ``$DAGSTER_HOME/dagster.yaml``.

This script will output a local configuration file at ``$DAGSTER_HOME/dagit-aws-config.yaml``, which
contains everything the script needs to manage your minimal cloud deploy and will look something
like this:

.. code-block:: YAML

    ec2:
      ami_id: ami-08fd8ae3806f09a08
      instance_id: i-07330e77c4dd1bc81
      key_file_path: /path/to/dagster-keypair-test-20200205T222824.pem
      key_pair_name: dagster-keypair-test-20200205T222824
      local_path: null
      region: us-west-1
      remote_host: ec2-54-67-22-239.us-west-1.compute.amazonaws.com
      security_group_id: sg-02cd3b76c352c2098
    rds:
      db_engine: postgres
      db_engine_version: '11.5'
      db_name: dagster
      instance_name: dagster-rds-test
      instance_type: db.t3.small
      instance_uri: dagster-rds-test.cldkwizddrkj.us-west-1.rds.amazonaws.com
      password: dWz9gDZWo2RQL7Dm
      storage_size_gb: 20
      username: dagster

Subsequent usage of the ``dagster-aws`` CLI tool on the same machine will use this configuration to
connect to your running EC2 instance.

You can look at
`init.sh <https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-aws/dagster_aws/cli/shell/init.sh>`_
for details on how we initialize the VM and how Dagit is run as a ``systemd`` service.

Once the EC2 instance is launched and ready, you can synchronize your Dagster code to it using:

.. code-block:: shell

    cd /path/to/your/dagster/code
    dagster-aws up

This command will copy the current directory to the remote host as ``/opt/dagster/app``, using rsync.
If there is a ``requirements.txt`` file present in the current directory, it will also install
those requirements on the remote host using ``pip install -r``. Finally, it will ensure Dagit is
running, and print a URL at which you can connect to Dagit.


Hosting Dagit on EC2 or ECS
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To host dagit on a bare VM or in Docker on ECS, see `Running Dagit as a service <local.html>`_.

Using RDS for run and event log storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use a hosted RDS PostgreSQL database for your Dagster run/events data. You can do
this by setting blocks in your ``$DAGSTER_HOME/dagster.yaml`` appropriately.

.. literalinclude:: dagster-pg.yaml
  :caption: dagster.yaml
   :language: YAML

In this case, you'll want to ensure you provide the right connection strings for your RDS instance,
and ensure that the node or container hosting Dagit is able to connect to RDS.

Be sure that this file is present, and `DAGSTER_HOME` is set, on the node where Dagit is running.

Note that using RDS for run and event log storage does not require that Dagit be running in the
cloud. If you are connecting a local Dagit instance to a remote RDS storage, double check that
your local node is able to connect to RDS.

Using S3 for intermediates storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable parallel computation (e.g., with the multiprocessing or Dagster celery executors), you
will also need to configure persistent intermediate storage -- for instance, using an S3 bucket
to store intermediates.

You'll first need to need to add S3 storage to your :py:class:`ModeDefinition`:

.. code-block:: python

    from dagster_aws.s3.resources import s3_resource
    from dagster_aws.s3.system_storage import s3_plus_default_storage_defs
    from dagster import ModeDefinition

    prod_mode = ModeDefinition(
        name='prod',
        system_storage_defs=s3_plus_default_storage_defs,
        resource_defs={'s3': s3_resource}
    )


Then, just add the following YAML block in your pipeline config:

.. code-block:: yaml

    storage:
      s3:
        config:
          s3_bucket: your-s3-bucket-name

With this in place, your pipeline runs will store intermediates on S3 in the location
``s3://<bucket>/dagster/storage/<pipeline run id>/intermediates/<solid name>.compute``
