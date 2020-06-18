# Instructions:

In the parent directory (`/docs`), run:

```
make buildnext
```

Then, in this directory, run:

```
yarn dev
```

The site should be live at https://localhost:3000

# Editing Docs

All documentation pages live under `src/pages/docs`. The path on the filesystem for an MDX file corresponds to the URL path. For example, the file `/pages/docs/deploying/aws.mdx` can be viewed at `localhost:3000/docs/deploying/aws`

The API documentation is still authored in the Sphinx project.

# New Syntax

Instead of RST, the docs are not written in MDX, which is just Markdown that can have inline React components.

## Links to API Docs

Previously:

```
:py:func:`@composite_solid <dagster.composite_solid>`
```

Now:

```
<PyObject module="dagster" object="composite_solid" displayText="@composite_solid" />
```

## Inline Code:

Previously:

```
.. code-block:: console

   $ dagit -f config.py -n config_pipeline
```

Now:

<pre>
```bash
$ dagit -f config.py -n config_pipeline
```
</pre>

## Literal includes:

Previously:

```
.. literalinclude:: ../../../examples/docs_snippets/docs_snippets/intro_tutorial/materializations.py
   :lines: 23-56
   :linenos:
   :lineno-start: 23
   :emphasize-lines: 24-33, 35
   :caption: materializations.py
   :language: python
```

Now:

<pre>
```python literalinclude showLines startLine=23 emphasize-lines=24-33,35 caption=materializations.py
file:/intro_tutorial/materializations.py
lines:23-56
```
</pre>
