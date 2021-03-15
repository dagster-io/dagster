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

.. autodata:: DataFrame
