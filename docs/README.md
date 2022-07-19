# Dagster Documentation Site

This directory contains the code for the Dagster documentation site at https://docs.dagster.io. The site is built with [NextJS](https://nextjs.org/), with the code for the site living in `next`. To serve the site locally in development mode (hot-reloading), run:

```
# only run the first time, to set up the site's environment
$ make next-dev-install  

# runs development server on localhost:3001, watching mdx in `content` dir and site code in `next`
$ make next-watch-build  
```

The content for the site is of several types and stored in several places:

- [**Prose docs**](#prose-docs) make up the majority of the docs site: Tutorials, Concepts, Guides, etc. All prose docs live directly in the `content` folder as `mdx` files (markdown with React components). You should edit these files directly to update prose docs.
- [**API docs**](#api-docs) contain the formal specification of Dagster's APIs. The built representation of the API docs consists of a few large JSON files in `content/api`. These files should not be edited directly-- they are the output of a build process that extracts the docstrings in Dagster source. The primary build tools are [Sphinx](https://www.sphinx-doc.org/en/master/) and its [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html). Sphinx processes a set of `rst` files (found in `sphinx/index.rst` and `sphinx/sections`) into JSON, which is then massaged into a (still-JSON) structure that NextJS can understand (`scripts/pack_json.py` script) and written to `content/api`. Note that there is little text in the `rst` files, because their main purpose is to invoke `autodoc` directives which pull in docstrings from all over the dagster codebase.
- [**Code snippets**](#code-snippets) are embedded throughout the prose docs. All code snippets used in the docs site live (outside the `docs` folder) in `examples/docs_snippets`. This is just a regular python package, which makes it easy to test and specify dependencies for the snippets.
- [**Screenshots**](#screenshots) are image files living in `next/public/images`, typically under a subdirectory corresponding to the page on which they appear. There's no need to manually manage the screenshots in this directory-- instead you can add a specification your screenshot to `screenshot_capture/screenshots.yaml` and run `screenshot_capture/capture_screenshot.py` to quasi-automatically generate the screenshot and place it in the appropriate subdirectory of `next/public/images`.
- [**Navigation schema**](#navigation-schema) is a JSON file specifying the contents of the main nav for the site (found in the left sidebar). This typically needs to be updated to include a link when new prose doc is added.

## Prose docs

We use MDX, which is a format that embeds JSX in markdown documents. This lets us import React components and embed them in our doc pages written in markdown. All of our prose docs live in `content`, where they are grouped into a few directories corresponding to the categories of docs shown in the left sidebar: `concepts`, `guides`, etc. There is a 1-1 correspondence of MDX files to pages in these categories.

Just as with code, we apply checks in CI to maintain the quality of our MDX files. Specifically, the full corpus of MDX is processed with `make mdx-format` and diffed against the source. If any discrepancies are found, the CI step will fail. Therefore you should always run `make mdx-format` before pushing MDX changes. `make mdx-format` processes all MDX files in `content`, performing several transformations (additional transformations can be added if needed):

- Formats MDX markdown and React code using [Prettier](https://prettier.io/).
- Transforms raw HTML `img` tags into special `Image` components (see [here](#embedding-images)).
- Resolves references to external code snippets and overwrites the corresponding code blocks with the external snippet.

See the subsections below for details.

### React components

The set of React components available to our MDX files is defined in `next/components/mdx/MDXComponents.tsx`. Note that the various other compenents defined in `next/components` _are not available to MDX_; if you want to use a component in MDX, it must be exported from `MDXComponents.tsx`.

MDX doesn't support imports, so components aren't imported into the MDX file in which they are used. Instead, the full set of `MDXComponents` components is injected into the build environment when the MDX is rendered to HTML (this happens in `next/pages/[...page].js`). 

You should browse `MDXComponents.tsx` to get a sense of what's available, but
the most commonly used component is the `<PyObject />` component. It is used to
link to references in the API docs from MDX files:

```
Here is an example of using PyObject: <PyObject module="dagster" object="SolidDefinition" />
By default, we just display the object name. To override, use the `displayText` prop: <PyObject module="dagster" object="asset" displayText="@asset"/ >
```

Finally, a note on updates to `MDXComponents.tsx`-- this has to be treated as a stable API, which means additive changes to components are allowed but breaking changes are not. This is because a single deployment of the docs site contains both the latest and older versions of the docs. The older versions are pulled off of Amazon S3 at build time. This means the sole `MDXComponents` instance needs to be compatible with both the current set of MDX files _and_ much older versions. For this reason, even if you update all callsites in the current MDX files after making a breaking change to a component, you will still break the docs site-- there are also callsites in the older docs versions archived on S3 that you cannot update.

### Embedding images

NextJS provides a special `Image` component that optimizes image-loading in production. We shadow and wrap this component with our own `Image` component defined in `MDXComponents`, which (1) adjusts the source path to account for version (images that are referenced in older doc versions but no longer present in `next/public/images` need to be pulled from S3); (2) wraps the image in a `Zoom` component, allowing image zoom on click.

Images may be sourced from either remote URLs or the site's static assets, which live in `next/public`. Paths to static images are rooted at `next/public`, e.g. `/images/some-image.png` refers to `next/public/images/some-image.png`. The vast majority of images used in the site are stored in `next/public/images` (see [Images and screenshots](#images-and-screenshots).

All images embedded in docs pages should use `MDXComponents.Image`, as opposed to a regular HTML `img` tag. Annoyingly, this component (due to the demands of NextJS `Image`) requires an explicit width and height to be set. Fortunately, we can automate the pulling of this information off the file. You can add simple `<img>` tags when writing docs, and they will be automatically converted to `MDXComponents.Image` when running `make mdx-format`. A `300x200` image stored in `next/public/images/some-image.png` could be referenced like this:

```
<img src="/images/some-image.png" />
```

And `make mdx-format` would transform it into this:

```
<Image src="/images/some-image.png" width=300 height=200 />
```

### Embedding external code snippets

Code snippets should not be authored directly in MDX files. This is because code in an MDX file is inaccessible to tooling and the Python interpreter, which makes it difficult to test and maintain. Our solution to this is to author code snippets in an external Python package (`examples/docs_snippets`) and reference these snippets from MDX files. This is done by creating an empty code block and providing the properties that act as an "address" for the code snippet within `docs_snippets`:

    ```python file=/some/file/in/docs_snippets.py startafter=a_start_marker endbefore=an_end_marker
    ```

The above points to a section of `examples/docs_snippets/docs_snippets/some/file/in/docs_snippets.py` delineated by line-comments specified by `startafter` and `endbefore` (note: both of these properties are optional):

    ### examples/docs_snippets/docs_snippets/some/file/in/docs_snippets.py

    ... code
    # a_start_marker
    ... code between a `a_start_marker` and `an_end_marker` is included in the snippet

    # an_end_marker
    ... code

Note that by default, extra whitespace between the ends of your snippet and the markers will be removed before injection into the MDX code block. You can pass the additional property `trim=false` to preserve the whitespace. You can also pass `dedent=<number of spaces>` to trim a leading number of spaces from each line in the snippet-- this is useful when you want to show e.g. an isolated method (indented in a class body) as a snippet. 

Running `make mdx-format` will inject referenced snippets into your code blocks. This will process _all_ MDX files in `content` and overwrite any existing body of any code block with a snippet reference. So be careful not to iterate on your code blocks inline in MDX-- always edit them in `docs_snippets`.

## API docs

The API documentation is authored in the `docs/sphinx` folder and built using [Sphinx](https://www.sphinx-doc.org/en/master/), a Python document generator. We use Sphinx because it has built-in functionality (the [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)) to document Python methods and classes by parsing docstrings.

If you update the API documentation in the `docs/sphinx` folder, you need to rebuild the output from Sphinx in order to see your changes reflected in the documentation site. This is enforced by our CI system, which will both verify that the docs build successfully and that the build output matches what is checked into the repository. This prevents merging docs source changes without the corresponding build.

The build is a two-step process. First, `sphinx-build` builds JSON (written to `docs/sphinx/_build/json`) from the `rst` source files in `docs/sphinx` (`index.rst` and everything in `sections`) (note that this JSON merely wraps Sphinx' typical HTML output, so you can still use Sphinx extensions to transform HTML). Second, we run a supplemental script `scripts/pack_json.py` that does two things: (a) transforms the Sphinx JSON into a form legible to NextJS; (b) writes the transformed JSON to `docs/content/api`. The final output is three JSON files in `docs/content/api`: `modules.json`, `searchindex.json`, and `sections.json`.

The most convenient way to build the API docs is to run `make apidoc-build` (from `dagster/docs`). This will execute the Sphinx build step using the `sphinx` tox environment (see `tox.ini`) and then run `scripts/pack_json.py` (only if the sphinx build executed with no warnings/errors). Note that it is important to use `tox` to run Sphinx rather than your normal dev environment-- that's because our Sphinx configuration requires a different set of packages than are installed by `scripts/install_dev_python_modules.py`.

If you are making changes to the API docs, you can use `make apidoc-watch-build` together with `make dev`. `apidoc-watch-build` uses the file watcher `watchmedo` (should be installed in your dev env from `watchdog`) to re-run `make apidoc-build` everytime either RST source or the sphinx configuration file changes. If it completes successfully, the updated API doc JSON will be picked up by the NextJS file watcher for `make dev` and trigger live reload of the docs site. This is very useful for experimenting with sphinx options and extensions.

### Mocking runtime dependencies

The Python environment in which Sphinx runs requires all targeted modules to be available on `sys.path`. This is because `autodoc` actually imports the modules during build (to access their docstrings). This means the Sphinx build process will also import anything else imported in the targeted modules. Thus `Sphinx` requires the entire graph of imports discoverable from your targets to be available on `sys.path`.

The simplest way to achieve this is to just install all of the target packages with `pip` into the Sphinx build environment, just as you would for a runtime environment. The problem is that, not all the packages you are targeting in the build can necessarily be installed into the same environment. That's often the case with our API docs-- a single run of Sphinx builds the API docs for _all_ dagster packages, and some of those extensions can have conflicting requirements.

`autodoc` provides a configuration option that can help here: `autodoc_mock_imports`. Every package listed in `autodoc_mock_imports` will be mocked during the Sphinx build, meaning that all imports from that package will return fake objects. Note that `autodoc_mock_imports` shadows the actual build environment-- if you have `foo` installed in the environment but `foo` is also listed in `autodoc_mock_imports`, imports will return mocks.

In a simpler world, we could simply put all dependencies of our build targets (Dagster packages) in `autodoc_mock_imports`. Unfortunately, it doesn't always work. If a dependency is used at import time and it is mocked, you will get an obscure Python error during the Sphinx build, as your code encounters a mocked object where it expects a different value from the library. For example, this is likely to crash the build because the value of `SOME_CONSTANT` is actually being _used_ at import time:

```python
from some_mocked_lib import SOME_CONSTANT

do_something(SOME_CONSTANT)
```

Whereas if `SOME_CONSTANT` is merely imported, then we can get away with mocking `some_mocked_lib`.

The solution used for our Sphinx environment is a compromise. We do a full editable install for any dagster package that uses any of its deps at build time. All other deps are mocked (see `autodoc_mock_imports` in `sphinx/conf.py`). This is not optimal in terms of having a lean build environment, because it brings in all other deps of a dagster package even if only one is used at import time. But it keeps our build environment simple, whereas a more targeted approach would have to cherry pick assorted deps and keep their version specifiers in sync with the corresponding dagster package.

## Images and screenshots

All non-remotely-sourced images should be stored in `next/public/images`. This directory is organized in a hierarchy that matches the structure of the prose docs, which keeps clear which images are used in which docs. For instance, images used in the `concepts/ops-jobs-graphs` pages are typically stored in `images/concepts/ops-jobs-graphs`.

### Screenshots

Most of the site's images are screenshots of Dagit. There is a semi-automated system in place to ease the generation and maintenance of screenshots. Screenshots are specified in "specs" which are stored in `screenshot/screenshots.yaml` as a flat array. Specs are objects with the following fields:

- `path`: output path (relative to `next/public/images`) indicating where the screenshot should be stored.
- `defs_file`: path (relative to the repo root) to a python or workspace YAML file. The script will pass the path to `dagit --python-file` or `dagit --workspace` (depending on file type) to load a set of Dagster definitions.
- `route`: Dagit route (i.e. path part of the URL) that will be loaded before taking a screenshot.
- `vetted`: boolean indicating whether the current screenshot in the repo was generated using the spec.
- `steps` (optional): manual steps that the person generating the screenshot should carry out before the screenshot is taken.
- `width` (optional): width in pixels of the browser window in which the screenshot will be taken.
- `height` (optional): height in pixels of the browser window in which the screenshot will be taken.

To generate the screenshot for a spec, pass its path to `screenshot/capture_screenshot.py`. This will attempt to render the specified Dagit view using the browser automation tool [Selenium](https://www.selenium.dev). If no `steps` are specified in the target spec, the screenshot will be taken and saved in `next/public/images` automatically. If `steps` were specified, after the initial Dagit view has rendered, the user will be prompted to execute the steps and then press a key to trigger screenshot capture and write. Note that successfully executing `capture_screenshot.py` will overwrite any existing image at the output path.

Note that to run `capture_screenshot.py` you need to have `selenium` installed in your Python environment, which in turn depends on a system package `chromedriver`. On macOS, this should work to install the dependencies:

```
$ pip install selenium
$ brew install chromedriver
$ xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver  # May not need to run this
```

## Navigation schema

If you are adding a new prose page or want to update the navigation in the sidebar, update the `docs/content/_navigation.json` file. The structure is self-explanatory when looking at the sidebar.
