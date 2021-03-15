Dask (dagster_dask)
===================

The ``dagster_dask`` module provides support for executing Dagster pipelines in Dask clusters, and using Dask as a resource to perform computations in solids. It also provides a DataFrame type with loaders and materializers so that you can easily work with DataFrames in solids.

Configuring Dask
----------------

The Dagster Dask executor and resource share a common configuration schema for creating a new Dask cluster or connecting to an existing Dask cluster. By default, :py:class:`a local cluster will be created <dask:distributed.deploy.local.LocalCluster>`. You can
configure the local cluster by explicitly providing a ``local`` cluster type config.

.. code-block:: yaml

  config:
    cluster:
      local:          # dask.distributed.LocalCluster parameters
        timeout: 5    # Timeout duration for initial connection to the scheduler
        n_workers: 4  # Number of workers to start

To connect to an existing Dask cluster, provide the scheduler address to the client.

.. code-block:: yaml

  config:
    client:
      address: tcp://127.0.0.1:8786

The following table lists the cluster types known to ``dagster-dask`` and their associated modules and classes.

=======  ========================================================  =====
Type     Module                                                    Class
=======  ========================================================  =====
local    :std:doc:`dask.distributed <dask-distributed:index>`      :py:class:`LocalCluster <dask:distributed.deploy.local.LocalCluster>`
ssh      :std:doc:`dask.distributed <dask-distributed:index>`      :py:func:`SSHCluster <dask:distributed.deploy.ssh.SSHCluster>`
azureml  :std:doc:`dask_cloudprovider <dask-cloudprovider:index>`  :py:class:`AzureMLCluster <dask-cloudprovider:dask_cloudprovider.azureml.AzureMLCluster>`
ecs      :std:doc:`dask_cloudprovider <dask-cloudprovider:index>`  :py:class:`ECSCluster <dask-cloudprovider:dask_cloudprovider.aws.ECSCluster>`
fargate  :std:doc:`dask_cloudprovider <dask-cloudprovider:index>`  :py:class:`FargateCluster <dask-cloudprovider:dask_cloudprovider.aws.FargateCluster>`
kube     :std:doc:`dask_kubernetes <dask-kubernetes:index>`        :py:class:`KubeCluster <dask-kubernetes:dask_kubernetes.KubeCluster>`
lsf      :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`LSFCluster <dask-jobqueue:dask_jobqueue.LSFCluster>`
moab     :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`MoabCluster <dask-jobqueue:dask_jobqueue.MoabCluster>`
oar      :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`OARCluster <dask-jobqueue:dask_jobqueue.OARCluster>`
pbs      :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`PBSCluster <dask-jobqueue:dask_jobqueue.PBSCluster>`
sge      :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`SGECluster <dask-jobqueue:dask_jobqueue.SGECluster>`
slurm    :std:doc:`dask_jobqueue <dask-jobqueue:index>`            :py:class:`SLURMCluster <dask-jobqueue:dask_jobqueue.SLURMCluster>`
yarn     :std:doc:`dask_yarn <dask-yarn:index>`                    :py:class:`YarnCluster <dask-yarn:dask_yarn.YarnCluster>`
=======  ========================================================  =====

To use other cluster types, ensure that the Python module for the type is installed. For example, to use the ``ecs`` type, install the ``dask_cloudprovider`` module. Refer to the class documentation for configuration options.

.. currentmodule:: dagster_dask

Executors
---------

The Dask executor runs Dagster pipelines as a graph of futures on a Dask cluster.

.. autodata:: dask_executor
  :annotation: ExecutorDefinition

See :ref:`Configuring Dask` for information about configuring a Dask executor, and the `Dask deployment guide <https://docs.dagster.io/deploying/dask/>`_ for information about using Dask for execution.

Resources
---------

.. autodata:: dask_resource
  :annotation: ResourceDefinition

See :ref:`Configuring Dask` for information about configuring a Dask resource.

Types
-----

The ``DataFrame`` type represents a Dask DataFrame for solid inputs and outputs. It includes loader and materialization support for reading and writing DataFrames in various formats. The following table lists the supported formats, along with their corresponding Dask DataFrame functions.

=========  ==============================================================  ========================
Type       Read Function (Loader)                                          To Method (Materializer)
=========  ==============================================================  ========================
csv        :py:func:`read_csv <dask:dask.dataframe.read_csv>`              :py:meth:`to_csv <dask:dask.dataframe.DataFrame.to_csv>`
parquet    :py:func:`read_parquet <dask:dask.dataframe.read_parquet>`      :py:meth:`to_parquet <dask:dask.dataframe.DataFrame.to_parquet>`
json       :py:func:`read_json <dask:dask.dataframe.read_json>`            :py:meth:`to_json <dask:dask.dataframe.DataFrame.to_json>`
fwf        :py:func:`read_fwf <dask:dask.dataframe.read_fwf>`
hdf        :py:func:`read_hdf <dask:dask.dataframe.read_hdf>`              :py:meth:`to_hdf <dask:dask.dataframe.DataFrame.to_hdf>`
orc        :py:func:`read_orc <dask:dask.dataframe.read_orc>`
sql_table  :py:func:`read_sql_table <dask:dask.dataframe.read_sql_table>`
sql                                                                        :py:meth:`to_sql <dask:dask.dataframe.DataFrame.to_sql>`
table      :py:func:`read_table <dask.dataframe.read_table>`
=========  ==============================================================  ========================

To configure a DataFrame input or output, specify a ``read`` or ``to`` key, respectively, along with the type, and type specific config options. Here is an example that configures the input ``data_df`` to read a Parquet dataset.

.. code-block:: yaml

  inputs:
    data_df:
      read:
        parquet:
          path: s3://bucket/data
          columns:
            - id
            - value
          filters:
            - - - year
                - '='
                - '2020'

Based on the :py:func:`dask.dataframe.read_parquet <dask:dask.dataframe.read_parquet>` documentation, this input config will read the ``id`` and ``value`` fields as columns from the ``year=2020`` partition of the Parquet dataset at ``s3://bucket/data``. For each laoder or materializer type, refer to its documentation (linked above) for the full set of options.

The loaders and materializers also support some utility functions for optimizing dataframes. For instance, the parquet dataset for the ``data_df`` input in the previous example might be partitioned into 8 parts. But, you have access to a Dask cluster with 32 worker nodes. In order to spread work to all 32 nodes, the dataframe should be repartitioned into at least 32 parts. This can accomplished by specifying ``repartition`` as part of the input config.

.. code-block:: yaml

  inputs:
    data_df:
      read:
        parquet:
          path: s3://bucket/data
        repartition:
          npartitions: 32

The ``repartition`` config corresponds to the Dask Dataframe :py:meth:`repartition <dask.dataframe.DataFrame.repartition>` method. The following table lists the supported utility methods.

======================  ======
Config Key              Options
======================  ======
drop                    See :py:meth:`drop <dask.dataframe.DataFrame.drop>`.
sample                  See :py:meth:`sample <dask.dataframe.DataFrame.sample>`.
reset_index             See :py:meth:`reset_index <dask.dataframe.DataFrame.reset_index>`.
set_index               See :py:meth:`set_index <dask.dataframe.DataFrame.set_index>`.
repartition             See :py:meth:`repartition <dask.dataframe.DataFrame.repartition>`.
normalize_column_names  If true, lowercases and converts CamelCase to snake_case on column names.
======================  ======

These utilities are not meant to replace equivalent code in solids. They are meant to help you create solids that are adaptable to different pipeline configurations. All of the options except for ``normalize_column_names`` map to the DataFrame methods of the same name.

.. autodata:: DataFrame
