Azure (dagster-azure)
---------------------

Utilities for using Azure Storage Accounts with Dagster. This is mostly aimed at Azure Data Lake
Storage Gen 2 (ADLS2) but also contains some utilities for Azure Blob Storage.


.. currentmodule:: dagster_azure

Resources
^^^^^^^^^^

.. autoconfigurable:: dagster_azure.adls2.ADLS2Resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_azure.adls2.FakeADLS2Resource
    :annotation: ResourceDefinition

.. autoclass:: dagster_azure.blob.AzureBlobComputeLogManager


I/O Manager
^^^^^^^^^^^

.. autoconfigurable::  dagster_azure.adls2.ADLS2PickleIOManager
  :annotation: IOManagerDefinition



File Manager (Experimental)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoconfigurable:: dagster_azure.adls2.adls2_file_manager
  :annotation: ResourceDefinition

.. autoclass:: dagster_azure.adls2.ADLS2FileHandle
  :members:


Legacy
^^^^^^^
.. autoconfigurable::  dagster_azure.adls2.ConfigurablePickledObjectADLS2IOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: dagster_azure.adls2.adls2_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_azure.adls2.adls2_pickle_io_manager
  :annotation: IOManagerDefinition