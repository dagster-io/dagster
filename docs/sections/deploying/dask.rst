Executing on Dask
-----------------

The `dagster-dask <https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dask>`__
module makes a :py:data:`~dagster_dask.dask_executor` available, which can target either a local
Dask cluster or a distributed cluster. Computation is distributed across the cluster at the
execution step level -- that is, we use Dask to orchestrate execution of the steps in a pipeline,
not to parallelize computation within those steps.

This executor takes the compiled execution plan, and converts each execution step
into a `Dask Future <https://docs.dask.org/en/latest/futures.html>`_ configured with the appropriate
task dependencies to ensure tasks are properly sequenced. When the pipeline is executed, these
futures are generated and then awaited by the parent Dagster process.

Data is passed between step executions via intermediate storage. As a consequence, a persistent
shared storage (such as a network filesystem shared by all of the Dask nodes, S3, or GCS) must be used.

Note that, when using this executor, the compute function of a single solid is still executed
in a single process on a single machine. If your goal is to distribute execution of workloads
`within` the logic of a single solid, you may find that invoking Dask or Pyspark directly from
within the body of a solid's compute function is a better fit than the engine layer covered in this
documentation.


Requirements
~~~~~~~~~~~~

Install `dask.distributed <https://distributed.readthedocs.io/en/latest/install.html>`_.

Local execution
~~~~~~~~~~~~~~~

It is relatively straightforward to set up and run a Dagster pipeline on local Dask. This can be
useful for test.

First, run ``pip install dagster-dask``.

Then, you'll need to add the dask executor to a :py:class:`ModeDefinition` on your pipeline:

.. literalinclude:: dask_hello_world.py
  :caption: dask_hello_world.py
  :language: python

Now you can run this pipeline with a config block such as the following:

.. literalinclude:: dask_hello_world.yaml
  :caption: dask_hello_world.yaml
  :language: YAML

Executing this pipeline will spin up local Dask execution, run the Dagster pipeline, and exit.

Distributed execution
~~~~~~~~~~~~~~~~~~~~~

If you want to use a Dask cluster for distributed execution, you will first need to
`set up a Dask cluster <https://distributed.readthedocs.io/en/latest/quickstart.html#setup-dask-distributed-the-hard-way>`_.
Note that the machine running the Dagster parent process must be able to connect to the host/port
on which the Dask scheduler is running.

You'll also need a persistent shared storage, which should be attached to a pipeline
:py:class:`~dagster.ModeDefinition` along with any resources on which it depends. (Here, we use the
:py:data:`~dagster_aws.s3_system_storage`)

For distributing task execution on a Dask cluster, you must provide a config block that includes the
address/port of the Dask scheduler:

.. literalinclude:: dask_remote.yaml
  :caption: dask_remote.yaml
  :language: YAML

Since Dask will invoke your pipeline code on the cluster workers, you must ensure that the latest
version of your Python code is available to all of the Dask workers. Ideally, you'll package this as
a Python module, and target your ``repository.yaml`` at this module.

Managing compute resources with Dask
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dask has [basic support](https://distributed.dask.org/en/latest/resources.html) for compute resource
management. In Dask you can specify that a particular worker node has, say, 3 GPUs, and then tasks
which are specified with GPU requirements will be scheduled to respect that constraint on available
resources.

In Dask, you'd set this up by launching your workers with resource specifications:

.. code-block:: shell

    $ dask-worker scheduler:8786 --resources "GPU=2"


and then when submitting tasks to the Dask cluster, specifying resource requirements in the Python
API:

.. code-block:: python

    client.submit(task, resources={'GPU': 1})


Dagster has simple support for Dask resource specification at the solid level for solids that will
be executed on Dask clusters. In your solid definition, just add `tags` as follows:

.. code-block:: python

    @solid(
        ...
        tags={'dagster-dask/resource_requirements': {"GPU": 1}},
    )
    def my_solid(_context, ...):
        pass

The dict passed to ``dagster-dask/resource_requirements`` will be passed through as the
``resources`` argument to the Dask client's :py:meth:`~dask:distributed.Client.submit` method for
execution on a Dask cluster. Note that in non-Dask execution, this key will be ignored.

Caveats
~~~~~~~

- For distributed execution, you must use a persistent intermediates storage such as S3 or GCS.
- Dagster logs are not yet retrieved from Dask workers; this will be addressed in follow-up work.

While this library is still nascent, we're working to improve it, and we are happy to accept
contributions.
