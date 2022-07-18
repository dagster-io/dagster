# Dagster Documentation Site

This folder contains the code for the Dagster documentation site at https://docs.dagster.io. The site is built with [NextJS](https://nextjs.org/), with the code for the site living in `next`. The content for the site lives in `content` and is of several types:

- **Prose docs** make up the majority of the docs site: Tutorials, Concepts, Guides, etc. All prose docs live directly in the `content` folder as `mdx` files (markdown with React components). You should edit these files directly to update prose docs.
- **API docs** contain the formal specification of Dagster's APIs. The built representation of the API docs consists of a few large JSON files in `content/api`. These files should not be edited directly-- they are the output of a build process that extracts the docstrings in Dagster source. The primary build tools are [Sphinx](https://www.sphinx-doc.org/en/master/) and its [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html). Sphinx processes a set of `rst` files (found in `sphinx/index.rst` and `sphinx/sections`) into JSON, which is then massaged into a (still-JSON) structure that NextJS can understand (`scripts/pack_json.py` script) and written to `content/api`. Note that there is little text in the `rst` files, because their main purpose is to invoke autodoc directives which pull in docstrings from all over the dagster codebase.
- **Code snippets** are embedded throughout our prose docs. All code snippets used in the docs site live (outside the `docs` folder) in `examples/docs_snippets`. This is just a regular python package, which makes it easy to test and specify dependencies for the snippets.
- **Screenshots** live in the 

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

Open http://localhost:3001/concepts/ops-jobs-graphs/ops in your browser, and the file `/content/concepts/ops-jobs-graphs/ops.mdx` in your editor. Try editing the file and see your changes be reflected live in the browser.

---

## Writing Documentation

- [Editing API Docs](#editing-api-docs): we use [Sphinx](https://www.sphinx-doc.org/en/master/) to generate API Docs.
- [Writing MDX](#writing-mdx): we use [MDX](https://mdxjs.com/table-of-components) to write our main
  content. This section will explain how to include [code snippets](#code-snippets-literal-includes)
  and use various [custom components](#using-components).
- [Navigation](#navigation): this explains how to update the sidebar.

<br />

### API Docs

The API documentation is authored separately in the `docs/sphinx` folder using [Sphinx](https://www.sphinx-doc.org/en/master/), a Python document generator. We use Sphinx because it has built-in functionality (the [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)) to document Python methods and classes by parsing the docstrings.

If you update the API documentation in the `docs/sphinx` folder, you need to rebuild the output from Sphinx in order to see your changes reflected in the documentation site. This is a two-step process. First, `sphinx-build` builds JSON (written to `docs/sphinx/_build/json`) from the `rst` source files in `docs/sphinx` (`index.rst` and everything in `sections`). Second, we run a supplemental script `scripts/pack_json.py` that does two things: (a) transform the Sphinx JSON into a form legible to Next.js; (b) write the transformed JSON to `docs/content/api`. The final output is three JSON files in `docs/content/api`: `modules.json`, `searchindex.json`, and `sections.json`.

The most convenient way to build the API docs is to run `make apidoc-build` (from `dagster/docs`). This will execute the sphinx build step using the `sphinx` tox environment (see `tox.ini`) and then run `scripts/pack_json.py` (only if the sphinx build executed with no warnings/errors). Note that it is important to use tox to run Sphinx rather than your normal dev environment-- that's because our Sphinx configuration requires a different set of packages than are installed by `scripts/install_dev_python_modules.py`.

If you are making changes to the API docs, you can use `make apidoc-watch-build` together with `make dev`. `apidoc-watch-build` uses the file watcher `watchmedo` (should be installed in your dev env from `watchdog`) to re-run `make apidoc-build` everytime either RST source or the sphinx configuration file changes. If it completes successfully, the updated API doc JSON will be picked up by the NextJS file watcher for `make dev` and trigger live reload of the docs site. This is very useful for experimenting with sphinx options and extensions.

TODO: How is this read by nextJS?

#### Sphinx environment: mocking imports

The Python environment in which Sphinx runs requires all targeted modules to be available on `sys.path`. This is because `autodoc` actually imports the modules during build (to access their docstrings). This it means the Sphinx build process will also import anything else imported in the targeted modules. Thus `Sphinx` requires the entire graph of imports discoverable from your targets to be available on `sys.path`.

The simplest way to achieve this is to just install all of the target packages with `pip` into the Sphinx build environment, just as you would for a runtime environment. The problem is that, not all the packages you are targeting in the build can necessarily be installed into the same environment. That's the case with our API docs-- a single run of Sphinx builds the API docs for _all_ dagster packages, and some of the extensions have conflicting requirements.

`autodoc` provides a configuration option that can help here: `autodoc_mock_imports`. Every package listed in `autodoc_mock_imports` will be mocked during the Sphinx build, meaning that all imports from that package will return fake objects. Note that `autodoc_mock_imports` shadows the actual build environment-- if you have `foo` installed in the environment but `foo` is also listed in `autodoc_mock_imports`, imports will return mocks.

In a perfect world, we could simply put all dependencies of our build targets (Dagster packages) in `autodoc_mock_imports`. Unfortunately, it doesn't always work. If a dependency is used at import time and it is mocked, you will get an obscure Python error during the Sphinx build, as your code encounters a mocked object where it expects a different value from the library. For example, this is likely to crash the build because the value of `SOME_CONSTANT` is actually being _used_ at import time:

```python
from some_mocked_lib import SOME_CONSTANT

do_something(SOME_CONSTANT)
```

Whereas if `SOME_CONSTANT` is merely imported, then we can get away with mocking `some_mocked_lib`.

The solution used for our Sphinx environment is a compromise. We do a full editable install for any dagster package that uses any of its deps at build time. All other deps are mocked (see `autodoc_mock_imports` in `sphinx/conf.py`). This is not optimal in terms of having a lean build environment, because it brings in all other deps of a dagster package even if only one is used at import time. But it keeps our build environment simple, whereas a more targeted approach would have to cherry pick assorted deps and keep their version specifiers in sync with the corresponding dagster package.

So long as a third-party dependency is listed in `autodoc_mock_imports`, it does not need to be installed in our sphinx environment.

We create the Sphinx environment by first installing from `docs-dagster-requirements.txt` with no dependencies, then installing Sphinx itself and its extensions from `docs-build-requirements.txt`. Most dependencies imported by dagster can go in the list of mocked imports in `autodoc_mock_imports` in `docs/sphinx/conf.py`, since they're not actually needed to build the docs, but the relatively small number of dependencies that are actually needed to import the dagster packages and build the docs can be found in `docs-build-requirements.txt`.

If you don't build the API documentation and include the changes in your diff, you will see a build error reminding you to do so.

If the test that checks whether the sphinx build passes is failing due to an import-related error, it likely indicates that a dependency needs to be added to `autodoc_mock_imports` in `conf.py` if it isn't actually needed to import the Dagster library (most common), or added to `docs-build-requirements.txt` if it actually needs to be included just for the library to be able to be imported (less common).

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

Run `make snapshot` to actually get the snippets to render. This will replace the body of the code block with the code you referenced.

**Important**: to change the value of a literal include, you must change the referenced code, not the code inside the code block. Run `make snapshot` once you update the underlying code to see the changes in the doc site. _This behavior is different from previous versions of the site._

**Properties:**

- **`file`**: The path to file relative to the `/examples/docs_snippets/docs_snippets` folder. You can use a relative path from this folder to access snippets from other parts of the codebase, but this is _highly discouraged_. Instead, you should copy the bit of code you need into `doc_snippets` and test it appropriately.
- **`startafter`** and **`endbefore`**: Use this property to specify a code snippet in between two markers. You will need to include the markers in the source file as comments.
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

### Generating and Updating Screenshots

Docs screenshots are generated manually. Previously, this meant that you would run Dagit and hit Shift-Command-4. Now, we are moving towards using the `docs/screenshot_capture/capture-screenshot.py` script, which adds some automation. To use it, you add a "screenshot spec" to `docs/screenshot_capture/screenshots.yaml` and then run the script to generate an image from that spec.

A screenshot spec includes:

- A `path` to an image file that the screenshot should be stored in.
- A `defs_file` that the script will run `dagit -f` or `dagit -w` on to load a set of Dagster definitions.
- A `url` for the page to take the screenshot from.
- An optional set of manual `steps`, which the person generating the screenshot is expected to carry out before the screenshot is taken.
- A `vetted` boolean, which indicates whether the current screenshot in the repo was generated using the spec.
- An optional `width` in pixels for the window in which the screenshot will be taken.
- An optional `height` in pixels for the window in which the screenshot will be taken.

#### Setup

```
pip install selenium
```

Install Selenium's chrome driver:

- `brew install chromedriver` OR download chromedriver from [here](https://chromedriver.chromium.org/downloads)) and manually add to /usr/local/bin
- You may need to run `xattr -d com.apple.quarantine /usr/local/bin/chromedriver` (gross)

#### Capturing a screenshot

Having written a screenshot spec, you can (re-)generate the screenshot by running the capture-screenshot script and providing the `path` value that you want to regenerate the screenshot for. E.g.

```
python docs/screenshot_capture/capture-screenshot.py concepts/dagit/runs-tab.png
```

It goes without saying that opportunities to automate this further abound.
