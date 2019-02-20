============
Dagstermill 
============

A wonderful feature of using Dagster is that you can productionize Jupyter notebooks and involve them in a (production) pipeline as units of computation. 

There are a few stages of data scientists using notebooks in the wild. 

1. Unstructured scratch work, cells are often run out of order.
2. More refined prototyping, where cells are run sequentially. Usually the top cells contain inputs and/or parameters that are used in later cells. 
3. Pieces of re-usable code are extracted from a notebook, turned into functions and put in a script (``.py`` file)

Typically, only stage 3 would be involved in a production pipeline. However, with dagstermill, if you have a notebook in stage 2 (i.e. the cells run sequentially to produce the desired output), with minimal effort you can register this notebook as a solid in the pipeline and use the notebook driven solid as a unit of computation in your pipeline that takes in inputs and produces outputs (that can be consumed by later stages of the pipeline).

An (Very Simple) Pipeline with a Notebook
------------------------------------------

Say you have a pipeline as shown below:

.. image:: test_add_pipeline.png

This is a very simple pipeline, where the solid ``return_one`` returns 1 and ``return_two`` returns 2. The notebook driven solid ``add_two_numbers`` simply adds two numbers and returns the result, as the name suggests.

The notebook might have a cell that looks like the following:

.. code-block:: python

    a = 3
    b = 5
    result = 3 + 5

Currently your notebook simply adds together the numbers ``3`` and ``5``, but in a more generic sense, your notebook is effectively a function that takes in inputs ``a`` and ``b`` and products output ``result``. To use the language of the dagster abstraction, it is a solid with inputs ``a``, ``b`` of dagster-type ``Int`` and with an ouput ``result`` of type ``Int``. 

To register this notebook as a dagster solid, we use the following lines of code.

.. code-block:: python

    from dagster import InputDefinition, OutputDefinition, Int
    import dagstermill as dm

    my_notebook_solid = dm.define_dagstermill_solid(
                                name='add_two_numbers',
                                notebook_path='/notebook/path/add_two_numbers.ipynb',
                                inputs = [
                                    InputDefinition(name='a', dagster_type=Int),
                                    InputDefinition(name='b', dagster_type=Int)
                                ],
                                ouputs = [OutputDefinition(Int)]
                            )

The function ``dm.define_dagstermill_solid()`` returns an object of type ``SolidDefinition`` that can be passed into ``PipelineDefinition`` objects. We see that its arguments are rather self-explanatory: 

* ``name``: the name of the solid 
* ``notebook_path``: the location of the notebook so that the dagster execution engine can run the code in the notebook
* ``inputs``, ``outputs``: the named and typed inputs and ouputs of the notebook as a solid

However, we also have to add some boilerplate to the notebook itself to make sure it plays nice with the dagstermill framework. The final notebook with the boilerplate looks as follows--we explain the boilerplate below.

.. image:: add_two_numbers.png

1. ``import dagstermill as dm`` imports the dagstermill library, which is necesary for the rest of the boilerplate
2. ``dm.register_repository()`` takes a repository definition (``define_example_repository()`` in this case) and lets the notebook know how to find the repository that contains the corresponding notebook-driven solid.
3. There is a tagged cell with the tag ``parameters`` that should contain **only** the inputs of the notebook-driven solid.
4.  If the notebook-driven solid has an output, then call ``dm.yield_result()`` with the result.

There is a helpful `Dagstermill CLI`_ that you can use to generate notebooks that will automatically contain the requisite boilerplate.

=====================
How Dagstermill Works
=====================

The way dagstermill works is by auto-injecting a cell that replaces the `parameters`-tagged cell with the runtime values of the inputs and then running the notebook using the papermill library (at <https://github.com/nteract/papermill>). A nice side-effect of using the papermill library to run the notebook is that the output is contained in an "output notebook", whereas the source notebook remains unchanged. However, since the output notebook is itself a valid Jupyter notebook, debugging can be done within the notebook context! Within dagit, after a solid that is a notebook has run, we provide a link to the output notebook, as seen below so that you can examine and play around with the output as needed (without modifying the source notebook).

-----------------------------------------
A (More Complicated) Dagstermill Pipeline
-----------------------------------------

The above pipeline was a very simplistic use-case of a dagster pipeline involving notebook-driven solids. Below we provide a more complicated example of a pipeline involving notebooks with outputs that are fed in as inputs into further steps in the pipeline. This is a particular compelling use-case of incorporating notebook-driven solids into a pipeline, as the user no longer has to manually marshall the inputs and outputs of notebooks manually. Instead, the dagster execution engine takes care of this for us! Let us look at the following machine-learning inspired pipeline.



=====================
Full Dagstermill API
=====================

The boilerplate necesary for a notebook involves some of the ``dagstermill`` API, but here we describe some more advanced API functionality.

.. code-block:: python 
    
    dm.register_repository(repository_defn)

.. code-block:: python

    dm.yield_result(result_obj, output_name="result")

.. code-block:: python

    dm.define_dagstermill_solid(
        name=name, 
        notebook_path, 
        inputs=None, 
        outputs=None, 
        config_field=None
    )

.. code-block:: python
    
    dm.get_context(config=None)

===============
Dagstermill CLI
===============

To assist you in productionizing notebooks, the dagstermill CLI will be helpful in adding boilerplate to existing notebooks to turn them into dagster solids (or creating notebooks from scratch with the requisite boilerplate).

To create a notebook when you know the repository, use the ``dagstermill create-notebook`` command. The notebook name is provided with the ``--notebook`` argument. A repository can be provided using the ``.yml`` file or the other command line options for specifying the location of a repository definition. If the repository is not provided, then the scaffolding ``dm.register_repository()`` is not inserted.

.. code-block:: console
    
    $ dagstermill create-notebook --notebook "notebook_name" -y repository.yml

Normally, the ``create-notebook`` command will prompt to ask if you want to over-write an existing notebook with the same name (if such a notebook exists). The ``--force-overwrite`` flag forces the over-write.

.. code-block:: console 

    $ dagstermill create-notebook --help

    Usage: dagstermill create-notebook [OPTIONS]

    Creates new dagstermill notebook.

    Options:
    -n, --fn-name TEXT          Function that returns either repository or
                                pipeline
    -m, --module-name TEXT      Specify module where repository or pipeline
                                function lives
    -f, --python-file TEXT      Specify python file where repository or pipeline
                                function lives.
    -y, --repository-yaml TEXT  Path to config file. Defaults to
                                ./repository.yml. if --python-file and --module-
                                name are not specified
    -note, --notebook TEXT      Name of notebook
    --force-overwrite           Will force overwrite any existing notebook or
                                file with the same name.
    --help                      Show this message and exit.

**TODO**: Currently we don't auto-inject the parameters cell if it doesn't exist, but we can change the CLI to do this.

Given a notebook that does not have the requisite scaffolding (perhaps a notebook created before knowing exact what dagster repository it belongs in), use the ``register-notebook`` command to specify an existing notebook and repository, and the CLI will inject the requiste cells in the notebook with the boilerplate for registering the repository and adding the parameters-tagged cell, if one doesn't exist. Note that this CLI command operates **in-place**, so the original notebook is modified!

.. code-block:: console

    $ dagstermill register-notebook --notebook path/to/notebook -y repository.yaml

Here is an example before and after: 

.. image:: pre_boilerplate_notebook.png

After calling 

.. code-block:: console

    $ ls
    pre_boilerplate_notebook.ipynb repository.yml
    $ dagstermill register-notebook --notebook pre_boilerplate_notebook.ipynb -y repository.yml

.. image:: post_boilerplate_notebook.png








