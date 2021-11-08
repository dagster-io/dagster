# Dagster Documentation Site

This folder contains the code for the Dagster documentation site at https://docs.dagster.io

## Getting Started

To install the dependencies required to run the docs, run the following in the `/docs` directory:

```
make docs_dev_install
```

Then, run the developer server in the same `/docs` directory:

```
make dev
```

Open http://localhost:3001 with your browser to see the result.

All content is in the `/content` folder.

**_Try it out_**

Open http://localhost:3001/concepts/solids-pipelines/solids in your browser, and the file `/content/concepts/solid-pipelines/solids.mdx` in your editor. Try editing the file and see your changes be reflected live in the browser.

---

## Writing Documentation

- [Editing API Docs](#editing-api-docs): we use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate API Docs.
- [Writing MDX](#writing-mdx): we use [MDX](https://mdxjs.com/table-of-components) to write our main
  content. This section will explain how to include [code snippets](#code-snippets-literal-includes)
  and use various [custom components](#using-components).
- [Navigation](#navigation): this explains how to update the sidebar.

<br />

### Editing API Docs

The API documentation is authored separately in the `dagster/docs/sphinx` folder using [Sphinx](https://www.sphinx-doc.org/en/master/), a Python document generator. We use Sphinx because it has built-in functionality to document Python methods and classes by parsing the docstrings.

If you update the API documentation in the `dagster/docs/sphinx` folder, you need to rebuild the output from Sphinx in order to see your changes reflected in the documentation site.

To rebuild the docs site, run in the docs dir:

```
tox -vv -e py38-sphinx
```

Sphinx requires all the modules for which it is building API docs to be installed, but doesn't
require their dependencies to be installed, as long as the Dagster modules can be imported. We create the
docs environment for Sphinx by first installing from `docs-dagster-requirements.txt` with no
dependencies, then installing any required dependecies from `docs-build-requirements.txt`. Most
dependencies imported by dagster can go in the list of mocked imports in `autodoc_mock_imports`
in `docs/sphinx/conf.py`, since they're not actually needed to build the docs, but the relatively
small number of dependencies that are actually needed to import the dagster packages and build the
docs can be found in `docs-build-requirements.txt`.

If you don't build the API documentation and include the changes in your diff, you will see a build error reminding you to do so.

If the test that checks whether the sphinx build passes is failing due to an import-related error,
it likely indicates that a dependency needs to be added to `autodoc_mock_imports` in `conf.py` if it isn't
actually needed to import the Dagster library (most common), or added to `docs-build-requirements.txt` if
it actually needs to be included just for the library to be able to be imported (less common)

<br />

### Writing MDX

We use MDX, which is a content format that lets us use JSX in our markdown documents. This lets us import components and embed them in our documentation.

#### Code Snippets (Literal Includes)

We want the code snippets in our documentation to be high quality. We maintain quality by authoring snippets in the `/examples/docs_snippets` folder and testing them to make sure they work and we don't break them in the future.

**Example:**
To include snippets from the code base, you can provide additional properties to the markdown code fence block:

Using markers:

    ```python file=/concepts/solids_pipelines/solid_definition.py startafter=start_solid_definition_marker_0 endbefore=end_solid_definition_marker_0
    ```

**Render:**

Run `make snapshot` to actually get the snipets to render. . This will replace the body of the code block with the code you referenced.

**Important**: to change the value of a literal include, you must change the referenced code, not the code inside the code block. Run `make snapshot` once you update the underlying code to see the changes in the doc site. _This behavior is different from previous versions of the site._

**Properties:**

- **`file`**: The path to file relative to the `/examples/docs_snippets/docs_snippets` folder. You can use a relative path from this folder to access snippets from other parts of the codebase, but this is _highly discouraged_. Instead, you should copy the bit of code you need into `doc_snippets` and test it appropriately.
- **`startafter`** and **`endbefore`**: Use this property to specify a code snippet in between to makers. You will need to include the markers in the source file as comments.
- **`lines`**: (This is highly discouraged) Use this property to specify a range of lines to include in the code snippet. You can also pass multiple ranges separated by commas.

  For example:

        ```python file=/concepts/solids_pipelines/solid_definition.py lines=1-10,12
        ```

- **`trim=true`**: Sometimes, our Python formatter `black` gets in the way and adds some spacing before the end of your snippet and the `endbefore` marker comment. Use trim to get rid of any extra newlines.

<br />

#### Using Components

Here are the available components we built to use in MDX:

- PyObject
- Link
- Check
- Cross
- LinkGrid
- LinkGridItem
- Warning
- Experimental
- CodeReferenceLink

See more details in the `/components/MDXComponents` file.

**PyObject Component**

The most important component is the `<PyObject />` component. It is used to link to references in the API documentation from MDX files.

Example usage:

```
Here is an example of using PyObject: <PyObject module="dagster" object="SolidDefinition" />
By default, we just display the object name. To override, use the `displayText` prop: <PyObject module="dagster" object="solid" displayText="@solid"/ >
```

<br />

### Navigation

If you are adding a new page or want to update the navigation in the sidebar, update the `docs/content/_navigation.json` file.
