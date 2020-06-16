
Flyte (Experimental) (dagster_flyte)
====================================

This library allows a user to define a dagster pipeline, and then pass the pipeline defintion to
a helper function or compiler that will compile the pipeline into a workflow object that can be executed
in `Flyte <https://github.com/lyft/flyte>`_.

At this time you will need to use type annotations on inputs and outputs of your pipeline. Currently,
only scalar dagster types and python primitives are supported.

Installation
------------

``pip install dagster_flyte``

Refer to this `Installation Guide <https://lyft.github.io/flyte/administrator/install/getting_started.html#getting-started>`_
for getting Flyte running locally using minikube.

Hello World
-----------

After creating a Flyte cluster and installing dagster-flyte you will likely need to set up a tunnel
with minikube.

``minikube service --alsologtostderr -v=3 contour -n heptio-contour``

Navigate to the ``\console`` route of the resultant URL and port for the flyte console.

Also, create a new flyte project:

``curl -X POST localhost:{{PORT}}/api/v1/projects -d '{"project": {"id": "project_name", "name": "project_name"} }'``

Next, define a pipeline. An easy way to start would be to cd into the examples directory in dagster-flyte.

``make docker_build``

``docker run --network host -e FLYTE_PLATFORM_URL='127.0.0.1:30081' {{IMAGE_ID}} pyflyte -p {{PROJECT_NAME}} -d development -c sandbox.config register workflows``

Return to the Flyte console and run your workflow from there.

.. currentmodule:: dagster_flyte

.. autofunction:: compile_pipeline_to_flyte
