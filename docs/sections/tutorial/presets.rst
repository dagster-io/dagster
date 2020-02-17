Pipeline config presets
-----------------------

Useful as the Dagit config editor and the ability to stitch together YAML fragments is, once
pipelines have been productionized and config is unlikely to change, it's often useful to distribute
pipelines with embedded config. For example, you might point solids at different S3 buckets in
different environments, or want to pull database credentials from different environment variables.

Dagster calls this a config preset:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/presets.py
   :lines: 128-167
   :linenos:
   :lineno-start: 128
   :caption: presets.py
   :emphasize-lines: 14-37
   :language: python

We illustrate two ways of defining a preset.

The first is to pass an ``environment_dict`` literal to the constructor. Because this dict is
defined in Python, you can do arbitrary computation to construct it -- for instance, picking up
environment variables, making a call to a secrets store like Hashicorp Vault, etc.

The second is to use the ``from_files`` static constructor, and pass a list of file globs from
which to read YAML fragments. Order matters in this case, and keys from later files will overwrite
keys from earlier files.

To select a preset for execution, we can use the CLI, the Python API, or Dagit.

From the CLI, use ``-p`` or ``--preset``:

.. code-block:: shell

    $ dagster pipeline execute -f presets.py -n presets_pipeline -p unittest

From Python, you can use :py:func:`execute_pipeline_with_preset <dagster.execute_pipeline_with_preset>`:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/presets.py
   :lines: 171
   :dedent: 4
   :language: python

And in Dagit, we can use the "Presets" selector.

.. thumbnail:: presets.png
