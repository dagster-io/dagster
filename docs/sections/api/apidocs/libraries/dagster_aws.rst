AWS (dagster_aws)
=================

.. currentmodule:: dagster_aws

S3
--

.. autoclass:: dagster_aws.s3.S3ComputeLogManager

.. autoclass:: dagster_aws.s3.S3FileCache
  :members:

.. autoclass:: dagster_aws.s3.S3FileHandle
  :members:

.. autodata:: dagster_aws.s3.s3_resource
  :annotation: ResourceDefinition

.. autodata:: dagster_aws.s3.S3Coordinate
  :annotation: DagsterType

  A :py:class:`dagster.DagsterType` intended to make it easier to pass information about files on S3
  from solid to solid. Objects of this type should be dicts with ``'bucket'`` and ``'key'`` keys,
  and may be hydrated from config in the intuitive way, e.g., for an input with the name
  ``s3_file``:

  .. code-block:: YAML

      inputs:
        s3_file:
          value:
            bucket: my-bucket
            key: my-key


.. autodata:: dagster_aws.s3.s3_system_storage
  :annotation: SystemStorageDefinition

.. autodata:: dagster_aws.s3.s3_plus_default_storage_defs
  :annotation: List[SystemStorageDefinition]

  The default system storages available on any :py:class:`~dagster.ModeDefinition` that does not
  provide custom system storages, i.e., :py:class:`~dagster.default_system_storage_defs` plus the
  :py:class:`s3_system_storage`.


Redshift
--------
.. autodata:: dagster_aws.redshift.redshift_resource
  :annotation: ResourceDefinition


Testing
^^^^^^^

.. autodata:: dagster_aws.redshift.fake_redshift_resource
  :annotation: ResourceDefinition


EMR
---

.. autodata:: dagster_aws.emr.emr_pyspark_step_launcher
  :annotation: ResourceDefinition

.. autoclass:: dagster_aws.emr.EmrJobRunner

.. autoclass:: dagster_aws.emr.EmrError

.. autodata:: dagster_aws.emr.EmrClusterState

.. autodata:: dagster_aws.emr.EmrStepState


CloudWatch
----------

.. autodata:: dagster_aws.cloudwatch.cloudwatch_logger
  :annotation: LoggerDefinition
