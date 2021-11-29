AWS (dagster-aws)
=================

.. currentmodule:: dagster_aws

S3
--

.. autoclass:: dagster_aws.s3.S3ComputeLogManager

.. autoclass:: dagster_aws.s3.S3FileCache
  :members:

.. autoclass:: dagster_aws.s3.S3FileHandle
  :members:

.. autoconfigurable:: dagster_aws.s3.s3_file_manager
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_aws.s3.s3_resource
  :annotation: ResourceDefinition

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

.. autoconfigurable:: dagster_aws.s3.s3_pickle_io_manager
  :annotation: IOManagerDefinition


Redshift
--------
.. autoconfigurable:: dagster_aws.redshift.redshift_resource
  :annotation: ResourceDefinition


Testing
^^^^^^^

.. autoconfigurable:: dagster_aws.redshift.fake_redshift_resource
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
