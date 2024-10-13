AWS (dagster-aws)
=================

Utilities for interfacing with AWS with Dagster.

.. currentmodule:: dagster_aws

S3
--

.. autoconfigurable:: dagster_aws.s3.S3Resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.s3.S3PickleIOManager
  :annotation: IOManagerDefinition

.. autoclass:: dagster_aws.s3.S3ComputeLogManager

.. autodata:: dagster_aws.s3.S3Coordinate
  :annotation: DagsterType

  A :py:class:`dagster.DagsterType` intended to make it easier to pass information about files on S3
  from op to op. Objects of this type should be dicts with ``'bucket'`` and ``'key'`` keys,
  and may be hydrated from config in the intuitive way, e.g., for an input with the name
  ``s3_file``:

  .. code-block:: YAML

      inputs:
        s3_file:
          value:
            bucket: my-bucket
            key: my-key



File Manager (Experimental)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dagster_aws.s3.S3FileHandle
  :members:

.. autoconfigurable:: dagster_aws.s3.S3FileManagerResource
  :annotation: ResourceDefinition


ECS
---
.. autoconfigurable:: dagster_aws.ecs.EcsRunLauncher
  :annotation: RunLauncher


Redshift
--------
.. autoconfigurable:: dagster_aws.redshift.RedshiftClientResource
  :annotation: ResourceDefinition


Testing
^^^^^^^

.. autoconfigurable:: dagster_aws.redshift.FakeRedshiftClientResource
  :annotation: ResourceDefinition


EMR
---

.. autoconfigurable:: dagster_aws.emr.emr_pyspark_step_launcher
  :annotation: ResourceDefinition

.. autoclass:: dagster_aws.emr.EmrJobRunner

.. autoclass:: dagster_aws.emr.EmrError

.. autodata:: dagster_aws.emr.EmrClusterState

.. autodata:: dagster_aws.emr.EmrStepState


CloudWatch
----------

.. autoconfigurable:: dagster_aws.cloudwatch.cloudwatch_logger
  :annotation: LoggerDefinition

SecretsManager
--------------

Resources which surface SecretsManager secrets for use in Dagster resources and jobs.

.. autoconfigurable:: dagster_aws.secretsmanager.SecretsManagerResource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.secretsmanager.SecretsManagerSecretsResource
  :annotation: ResourceDefinition

Pipes
--------------

Context Injectors
^^^^^^^^^^^^^^^^^

.. autoclass:: dagster_aws.pipes.PipesS3ContextInjector

.. autoclass:: dagster_aws.pipes.PipesLambdaEventContextInjector

Message Readers
^^^^^^^^^^^^^^^

.. autoclass:: dagster_aws.pipes.PipesS3MessageReader

.. autoclass:: dagster_aws.pipes.PipesCloudWatchMessageReader
   :members: consume_cloudwatch_logs

Clients
^^^^^^^

.. autoclass:: dagster_aws.pipes.PipesLambdaClient

.. autoclass:: dagster_aws.pipes.PipesGlueClient

.. autoclass:: dagster_aws.pipes.PipesECSClient

Legacy
--------

.. autoconfigurable:: dagster_aws.s3.ConfigurablePickledObjectS3IOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: dagster_aws.s3.s3_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.s3.s3_pickle_io_manager
  :annotation: IOManagerDefinition

.. autoconfigurable:: dagster_aws.s3.s3_file_manager
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.redshift.redshift_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.redshift.fake_redshift_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.secretsmanager.secretsmanager_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.secretsmanager.secretsmanager_secrets_resource
  :annotation: ResourceDefinition
