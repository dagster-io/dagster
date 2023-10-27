################################
Weights & Biases (dagster-wandb)
################################

This library provides a Dagster integration with `Weights & Biases <https://wandb.ai/>`_.

Use Dagster and Weights & Biases (W&B) to orchestrate your MLOps pipelines and maintain ML assets.

----

The integration with W&B makes it easy within Dagster to:

* use and create `W&B Artifacts <https://docs.wandb.ai/guides/artifacts>`_.
* use and create Registered Models in the `W&B Model Registry <https://docs.wandb.ai/guides/models>`_.
* run training jobs on dedicated compute using `W&B Launch <https://docs.wandb.ai/guides/launch>`_.
* use the `wandb <https://github.com/wandb/wandb>`_ client in ops and assets.

************
Useful links
************

For a complete set of documentation, see `Dagster integration <https://docs.wandb.ai/guides/integrations/dagster>`_ on the W&B website.

For full-code examples, see `examples/with_wandb <https://github.com/dagster-io/dagster/tree/master/examples/with_wandb>`_ in the Dagster's Github repo.

.. currentmodule:: dagster_wandb

********
Resource
********

.. autoconfigurable:: wandb_resource
  :annotation: ResourceDefinition

***********
I/O Manager
***********

.. autoconfigurable:: wandb_artifacts_io_manager
  :annotation: IOManager

Config
======

.. autoclass:: WandbArtifactConfiguration

.. autoclass:: SerializationModule

Errors
======

.. autoexception:: WandbArtifactsIOManagerError

***
Ops
***

.. autofunction:: run_launch_agent

.. autofunction:: run_launch_job
