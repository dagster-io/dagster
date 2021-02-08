# Instructions

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

All documentation pages live under `src/pages`. The path on the filesystem for an MDX file corresponds to the URL path. For example, the file `/pages/deploying/aws.mdx` can be viewed at `localhost:3000/deploying/aws`

The API documentation is still authored in the Sphinx project.

# New Syntax

Instead of RST, the docs are now written in MDX, which is just Markdown that can have inline React components.

## Links to API Docs

Previously:

```
:py:func:`@composite_solid <dagster.composite_solid>`
```

Now:

```
<PyObject module="dagster" object="composite_solid" displayText="@composite_solid" />
```

## Inline Code

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

## Literal includes

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

Or, you can use Python comment markers (instead of line numbers) which will prevent future changes from causing line numbers to drift and messing up the rendering of existing literal includes.

<pre>
```python literalinclude caption=materalizations.py
file:/intro_tutorial/materializations.py
startAfter:start_materialization_solids_marker_0
endBefore:end_materialization_solids_marker_0
```
</pre>

Python comment markers would live in your code like this:

```python
# materializations.py


excluded_int = 1

# start_materialization_solids_marker_0
def included_func():
   return 1
# end_materialization_solids_marker_0

excluded_bool = True

```

# Screenshots

Use [generate_screenshots.test.js](https://github.com/dagster-io/dagster/issues/3292#issue-751044712) to add or update screenshots in the documentation.

## Update screenshots

To update the screenshots, in the `/docs` directory, run:

```
npm run screenshots
```

When there is any change of the path of a screenshot or change of Dagit URLs, edit the generate_screenshots test. To update the changes, run:

```
npm run screenshots -- -u
```

## Add screenshots

Create a new test in [generate_screenshots.test.js](https://github.com/dagster-io/dagster/issues/3292#issue-751044712) to generate new screenshots.

Then, run `npm run screenshots -- -u`.
