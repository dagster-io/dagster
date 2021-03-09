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

Open http://localhost:3000 with your browser to see the result.

All content is in the `/content` folder.

**_Try it out_**

Open http://localhost:3000/concepts/solids-pipelines/solids in your browser, and the file `/content/concepts/solid-pipelines/solids.mdx` in your editor. Try editing the file and see your changes be reflected live in the browser.

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

In the `dagster/docs` directory (not this directory), run:

```
make build
```

If you don't build the API documentation and include the changes in your diff, you will see a build error reminding you to do so.

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
