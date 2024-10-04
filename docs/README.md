# Running the docs, v2

> **Submitting a pull request to update the docs?** If so, please verify that the updates follow the [docs style checklist](https://github.com/dagster-io/dagster/blob/master/docs/DOC_CHECKLIST.md).

This directory contains the code for the Dagster documentation site at https://docs.dagster.io. The site is built with [NextJS](https://nextjs.org/), with the code for the site living in `next`. To serve the site locally in development mode (hot-reloading), run:

---

## Getting started

To run the Dagster docs locally, you'll need to install [NodeJS](https://nodejs.org/en/download/). The version must be 12.13.0 or later.

After NodeJS is installed:

1. Clone the [`dagster-io/dagster` GitHub repository](https://github.com/dagster-io/dagster) to your local machine.
2. Using the Terminal, navigate to the `/docs` directory in the repository and run the following to set up the site's environment:
    
    ```bash
    make next-dev-install
    ```
    
    **Note**: This is the only time you’ll need to run this command.
    
3. Next, start the development server:
    
    ```bash
    make next-watch-build
    ```
    
    This command also enables hot-reloading, which automatically reloads `localhost:3001` when files in `/content` or `/docs/next` are modified.
    
4. Navigate to [https://localhost:3001](https://localhost:3001/) to view a live, rendered version of the docs.

---

## About

- [Page architecture][docs-page-architecture]
- [Directory structure][docs-site-structure]
- [Site technologies][docs-site-technologies]

### Page architecture

![docs-components.png](/docs/next/public/images/readme/docs-components.png)

### Directory structure

```yaml
/
├── /docs
│   ├── /content
│   │   ├── /api
│   │   ├── /[other content folders]
│   │   ├── _apidocs.mdx
│   │   ├── _navigation.json
│   │   └── [other-pages].mdx
│   ├── /dagit-screenshot
│   ├── /next
│   │   ├── /components
│   │   ├── /layouts
│   │   ├── /pages
│   │   ├── /public
│   │   ├── /scripts
│   │   ├── /styles
│   │   └── /util
│   ├── /node_modules
│   ├── /screenshots
│   ├── /scripts
│   └── /sphinx
└── /examples
    └── /docs_snippets
```

The following table contains information about the folders you’ll most commonly work in when editing the docs. **Note**: This isn’t an exhaustive list, as it’s unlikely folders and files not in this list will be touched.

Click the links in the **Path** column to learn more about a specific folder, its contents, and what it’s used for:

| Path | Description |
| --- | --- |
| [/content][docs-content] | All site content, including the site's navigation (`_navigation.json`). This folder primarily contains `.mdx` files, which are Markdown files with React components. To update doc content, directly edit these files. |
| [/dagit-screenshot][dagit-screenshot] | The Python module for the `dagit-screenshot` CLI tool. Used for automating screenshots from a local Dagit instance. |
| /next | The NextJS code that powers the site, including MDX components, redirects, images and other assets, etc. |
| [/screenshots][dagit-screenshot] | YAML configuration files used by dagit-screenshot. |
| [/sphinx][api-docs] | Specification files in ReStructured Text (`.rst`) used by Sphinx to generate API docs. |
| [/examples/docs_snippets][docs-code-snippets] | A Python package containing the code snippets embedded throughout the docs. |

### Site technologies

| Name | Usage | Notes |
| :--- | :--- | :--- |
| Algolia | Search |  |
| Google Analytics | Analytics |  |
| MDX | Content formatting | A file format that embeds JSX into Markdown files, supporting the import of React components. |
| NextJS | Site framework | A React framework used to build web applications. |
| Prettier | Code formatter | Run as part of the make [make mdx-format][mdx-format] CLI command, Prettier formats content in MDX files. |
| Remark | Markdown processor |  |
| Sphinx | API docs |  |
| Tailwind | CSS |  |
| Vercel | CDN | Hosts the docs. Vercel automatically deploys every push by default, including pushes to `master` and other branches, such as PRs.<ul><li>**Production branch**: `master`. Every push to `master` automatically deploys to [docs.dagster.io](https://docs.dagster.io).</li><li>**Preview branches**: For every push to a non-production branch, Vercel automatically builds and deploys a preview version of the docs. This is useful for debugging and previewing content changes.</li></ul> |
| YAML | Page metadata |  |
| Yarn | TODO |  |

---

## Development

- [Local][docs-development-local]
- [Pull requests][docs-pull-requests]

### Local

We apply CI checks to maintain the quality of our MDX files and code snippets. To ensure your code passes our CI checks, we recommend following this workflow when pushing changes:

#### 1. Run make black isort

Applicable only to code snippet changes in `/../examples/docs_snippets/docs_snippets`. Skip if no code snippet changes have been made.

```bash
# run in repo root
make black isort
```

#### 2. Run yarn test

This command runs internal and external link tests, failing when invalid links are detected.

```bash
cd /docs/next
yarn test
```

#### 3. Run make mdx-format

This command processes the full corpus of MDX files in `/content` and diffs them against the source, performing several transformations:

- Format MDX markdown and React code using [Prettier](https://prettier.io/)
- Transform Markdown images (`![]()`) and raw HTML `img` tags into special `Image` components. Refer to the Embedding images section for more info.
- Resolve references to external code snippets and overwrite the corresponding code blocks with the external snippet. Refer to the Embedding code snippets section for more info.

```bash
cd /docs
make mdx-format
```

If any discrepancies are found after the changes have been pushed, the associated CI step will fail.

We recommend running this command after other commands and immediately before pushing MDX changes. This ensures that code snippet changes are correctly reflected in MDX files, avoiding a failed CI test.

#### 4. Push

After the previous steps are completed, you can push your changes and, if you haven’t already, open a pull request.

### Pull requests

For every push made to a pull request, Vercel automatically deploys a preview version of the docs. This is useful for debugging and previewing content changes.

In the pull request, click the **Visit Preview** link to view the preview:

![Vercel 'Visit preview' link](/docs/next/public/images/readme/vercel-visit-preview-link.png)

When your pull request is ready for review, add @erinkcochran87 as a reviewer. You can also add other Dagster maintainers, but Erin is required for all documentation reviews.

---

## Authoring

In this section, we’ll cover the different types of content in the Dagster docs and how to work with the site navigation.

The Dagster docs have two types of doc content:

- [General][docs-content], which are MDX files in the `/content` folder
- [API][api-docs], which are auto-generated from Python docstrings in the Dagster codebase using Sphinx

### General/MDX content

<details><summary><strong>Relevant CLI commands</strong></summary>
        
| Command | Run location | Usage | Description |
| :--- | :--- | :--- | :--- |
| make next-dev-install | /docs | Local dev | Sets up the site's environment. Only required after the initial install. |
| make next-watch-build | /docs | Local dev | Runs the development server on `localhost:3001`. Watches MDX files in `/content` and site code in `/docs/next`. |
| make mdx-format | /docs | Content | Runs [/docs/next/scripts/mdx-transform.ts][mdx-format-source], which formats MDX and React code. This includes standardizing MDX content, inserting code snippet content into code blocks, transforming HTML `img`/Markdown images into React `Image` components. Run immediately prior to committing changes to prevent a Buildkite error.<br><br>**Note:** If you’ve edited code snippets, you should run `make black isort` before running this and committing changes. Our CI checks the contents of code snippets in MDX against their source files and fails if there’s a mismatch. If running `black` and `isort` make changes to your code snippets, running `mdx-format` last ensures that there won’t be a mistmatch due to formatting. |
| make black | / | Code snippets | Runs [TODO]. If you've added or editing code snippets, run immediately prior to committing changes. |
| make isort | / | Code snippets | Runs [TODO]. If you've added or editing code snippets, run immediately prior to committing changes. |
| yarn test | /docs/next | Content | Runs some [testing scripts][link-tests], which tests the validity of internal and external links. |
</details>

The `/content` directory contains the bulk of the docs’ content, such as tutorials, guides, references, and so on. **Note**: API documentation doesn’t live in this folder - API docs are managed differently than general doc pages. Refer to the [API docs section][api-docs] for more info.

All general doc pages are saved as `.mdx` files, which are [Markdown](https://www.markdownguide.org/) files that contain YAML Frontmatter and React components. MDX is a format that embeds JSX in Markdown files, allowing us to import [React components][next-components] and use them in Markdown content. For example:

```markdown
<!-- YAML Frontmatter -->
---
title: "Getting started with Dagster Cloud | Dagster Docs"
description: "Learn how to get up-and-running with Dagster Cloud."
---

<!-- Page content and React components -->

# Page title

Content here! 

<!-- Example component -->

<Experimental />
```

Each MDX file in `/content` directly corresponds to a single, rendered docs page where the file path is used to construct the page’s final URL. For example:

- [**Prose docs**](#prose-docs) make up the majority of the docs site: Tutorials, Concepts, Guides, etc. All prose docs live directly in the `content` folder as `mdx` files (markdown with React components). You should edit these files directly to update prose docs.
- [**API docs**](#api-docs) contain the formal specification of Dagster's APIs. The built representation of the API docs consists of a few large JSON files in `content/api`. These files should not be edited directly-- they are the output of a build process that extracts the docstrings in Dagster source. The primary build tools are [Sphinx](https://www.sphinx-doc.org/en/master/) and its [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html). Sphinx processes a set of `rst` files (found in `sphinx/index.rst` and `sphinx/sections`) into JSON, which is then massaged into a (still-JSON) structure that NextJS can understand (`scripts/pack_json.py` script) and written to `content/api`. Note that there is little text in the `rst` files, because their main purpose is to invoke `autodoc` directives which pull in docstrings from all over the dagster codebase.
- [**Code snippets**](#code-snippets) are embedded throughout the prose docs. All code snippets used in the docs site live (outside the `docs` folder) in `examples/docs_snippets`. This is just a regular python package, which makes it easy to test and specify dependencies for the snippets.
- [**Screenshots**](#screenshots) are image files living in `next/public/images`, typically under a subdirectory corresponding to the page on which they appear. There's no need to manually manage the screenshots in this directory-- instead you can add a specification your screenshot to `screenshots` and run `dagster-ui-screenshot capture` to quasi-automatically generate the screenshot and place it in the appropriate subdirectory of `next/public/images`.
- [**Navigation schema**](#navigation-schema) is a JSON file specifying the contents of the main nav for the site (found in the left sidebar). This typically needs to be updated to include a link when new prose doc is added.
- [**Dagster University**](#dagster-university) is a separate Nextjs site containing the content for Dagster University courses. 

Refer to the [Development section][docs-development] for info about committing and pushing MDX changes.

### Page elements / components

In [`/next/components/mdx/MDXComponents.tsx`][next-components-source], you’ll find the React components available for use in MDX files. **Note**: Other components in `/next/components` can’t be used in MDX files. To use a component in an MDX file, **it must be exported from `MDXComponents.tsx`.**

As MDX doesn’t support imports, components aren’t imported into the MDX file in which they’re used. Instead, the full set of `MDXComponents` components is injected into the build environment when the MDX is rendered to HTML, which happens in [`/next/pages/[...page].tsx`][next-page-tsx].

> ‼️ **Making updates to `MDXComponents.tsx`**
>
> This file must be treated as a stable API, which means only **additive** changes are allowed. Breaking changes will break the docs site. 
>
> This is due to how the site handles versioning: A single deployment of the docs site contains both the latest version **and** all older versions. Older versions are pulled from Amazon S3 at build time, meaning that the sole `MDXComponents.tsx` instance must be compatible across all doc versions. This means that even if all callsites in the current MDX files are updated after making a breaking change, there are still callsites in the archived versions on S3 that can’t be updated.
> 
> TL:DR; No breaking changes to `MDXComponents.tsx`, or you’ll break the site. 😟

The following sections contain info about the most commonly used components, how to use them, and the impact `make mdx-format` has when run.

| Component | Description |
| --- | --- |
| [PyObject][component-pyobject] | Creates auto-linking references to API docs in MDX files. |
| [Image][component-image] | Embeds images in MDX files. |
| [Code snippet][component-code-snippet] | Embeds code snippets in MDX files. |
| [Callout][component-callout] | Creates callout boxes in MDX files. |
| [Article list][component-article-list] | Creates a two-column list of links in MDX files. |
| [Tabs][component-tabs] | Creates a tabbed interface in MDX files. |

#### PyObject

The most commonly used component is the `PyObject` component. When used, this component automatically creates references to the API docs from MDX files.

`PyObject` should be used whenever possible, as it:

- Pulls object names directly from the code base, ensuring the correct name is always used
- Simplifies linking to supporting API reference content

The following table describes the properties accepted by `PyObject` and demonstrates how to use them:

<table>
<thead>
  <tr>
    <th>Name</th>
    <th>Required?</th>
    <th>Description</th>
    <th>Example</th>
  </tr>
</thead>
<tbody>
  <tr>
<td valign="top">object</td>
<td valign="top">Yes</td>
<td valign="top">The name of the Python object. By default, the object name is also used as the display text./td>
<td valign="top">
    
```
Example:
<PyObject object="Definitions" /> 

Result:
[Definitions](/_apidocs/definitions#Definitions)
```

</td>
  </tr>
  <tr>
<td valign="top">module</td>
<td valign="top">Yes*</td>
<td valign="top">

Required if the object exists outside of the core Dagster module. The name of the Python module containing the object. For example, `dagster_airbyte`     

</td>
<td valign="top">
    
```
Example:
<PyObject module="dagster_dbt" object="DbtCliResource" />

Result:
[DbtCliResource](/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtCliResource)
```

</td>
  </tr>
  <tr>
<td valign="top">displayText</td>
<td valign="top">No</td>
<td valign="top">
    
If provided, the value of `displayText` will be used as display text instead of the object’s name.

</td>
<td valign="top">
    
```
Example:
<PyObject object="Definitions" displayText="code location" />

Result:
[code location](/_apidocs/definitions#Definitions)
```

</td>
  </tr>
  <tr>
<td valign="top">pluralize</td>
<td valign="top">No</td>
<td valign="top">
    
If provided, the object (or `displayText`, if provided) will be pluralized.

</td>
<td valign="top">
    
```
Example:
<PyObject object="Definitions" displayText="code location" pluralize />

Result:
[code locations](/_apidocs/definitions#Definitions)
```

</td>
  </tr>
  <tr>
<td valign="top">method</td>
<td valign="top">No</td>
<td valign="top">If provided, the object value will be formatted as a Python method.</td>
<td valign="top"></td>
  </tr>
    <tr>
<td valign="top">decorator</td>
<td valign="top">No</td>
<td valign="top">If provided, the value of object will be formatted as a Python decorator.</td>
<td valign="top">
    
```
Example:
<PyObject object="asset" decorator />

Result:
[@asset](/_apidocs/assets#dagster.asset)
```

</td>
  </tr>
</tbody>
</table>


### Images

#### General

Images:

- Can be sourced from either remote URLs or the site’s static assets (`/docs/next/public/images`)
- Used in MDX files with either Markdown or HTML syntax
- Should have descriptive `alt` text
- Should have descriptive file names. For example: `dagit-asset-catalog-stale-assets.png`
- Should be used with sparingly and with intention, especially for UI screenshots (of Dagit or any other application). Being selective helps reduce the number of outdated and potentially confusing images in the docs.

Paths to static images are rooted at `/next/public`, e.g. `/images/some-image.png` refers to `/next/public/images/some-image.png`. The vast majority of images used in the site are stored in `/next/public/images`.

Markdown or HTML syntax can be used to add images to MDX files. For example:

```markdown
## Markdown
![Alt text](/images/some-image.png)

## HTML
<img src="/images/some-image.png" alt="Alt text" />
```

#### make mdx-format transformation

When `make mdx-format` is run, all images formatted using Markdown or HTML will be converted to a React `Image` component, defined in `MDXComponents.tsx`. This custom component wraps a special NextJS `Image` component that optimizes image loading in production, and does the following:

1. Adjusts the source path to account for version. Specifically, images referenced in older doc versions but are no longer present in `next/public/images` need to be pulled from S3.
2. Wraps the image in a `Zoom` component, allowing image zoom on click

Additionally, our custom `Image` component - due to the demands of NextJS `Image` - requires explicit width and height to be set for every image. When `make mdx-format` is run, the script will detect image tags, pull image widths and heights from file information, and convert them to `Image` components.

For example, the above example images would be transformed to:

```markdown
<Image src="/images/some-image.png" alt="Alt text" width=300 height=200 />
```

> ‼️ A limitation of `make mdx-format` is that width and height changes aren’t detected in `Image` components. This means that if an image is replaced and its dimensions have changed, you’ll need to first format the image using Markdown or HTML and then run `make mdx-format` to pull the correct dimensions.

### Code snippets

<details><summary><strong>Relevant CLI commands</strong></summary>

| Command | Run location | Usage | Description |
| --- | --- | --- | --- |
| make black | / | Code snippets | Runs [TODO]. If you've added or editing code snippets, run immediately prior to committing changes. |
| make isort | / | Code snippets | Runs [TODO]. If you've added or editing code snippets, run immediately prior to committing changes. |
| make mdx-format | /docs | Content | Runs [`/next/scripts/mdx-transform.ts`][mdx-format-source], which formats MDX and React code. This includes standardizing MDX content, inserting code snippet content into code blocks, transforming HTML `img`/Markdown images into React `Image` components. Run immediately prior to committing changes to prevent a Buildkite error.<br><br>**Note**: If you’ve edited code snippets, you should run make black isort before running this and committing changes. Our CI checks the contents of code snippets in MDX against their source files and fails if there’s a mismatch. If running black and isort does make changes to your code snippets, running mdx-format last ensures that there won’t be a mistmatch due to formatting. |
</details>

#### General

Code snippets:

- Live in `/../examples/docs_snippets`. This is a Python package that allow us to test and specify dependencies for the snippets.
- **Should not be authored directly in MDX files.** Code in MDX files is inaccessible to tooling and the Python interpreter, which makes testing and maintenance difficult.
- Should (generally) have an accompanying test in `/../examples/docs_snippets/docs_snippets_tests`.  Our CI runs these tests against code snippets in `/../examples/docs_snippets/docs_snippets` and will fail if errors occur.

To reference a code snippet, create an empty code block:

````
```
python file=/concepts/assets/asset_dependency.py startafter=start_marker endbefore=end_marker
```
````

And provide the following properties:

- `file` - The file path to the code snippet file, relative to `/../examples/docs_snippets/docs_snippets`
- `startafter` - **Optional**. Useful if including multiple snippets in a single file. This property defines the starting point of the code snippet; everything between this marker and `endbefore` will be included.
- `endbefore` - **Optional**. Useful if including multiple snippets in a single file. This property defines the ending point of the code snippet; everything between this marker and `startafter` will be included.
- `trim` - **Optional**. If `false`, extra whitepsace at the ends of the snippet will be preserved. Whitespace is removed by default unless otherwise specified.
- `dedent` - **Optional**. Trims the specified number of leading spaces from each line in the snippet. For example, `dedent=4` would trim `4` spaces from each line in the snippet. This is useful for showing an isolated method (indented in a class body) as a snippet.

The above example points to the following section of `/../examples/docs_snippets/docs_snippets/concepts/assets/asset_dependency.py`:

https://github.com/dagster-io/dagster/blob/b2b5f563069d476f519da5f188b47ba14c014495/examples/docs_snippets/docs_snippets/concepts/assets/asset_dependency.py#L5-L16

#### make mdx-format transformation

When you run `make mdx-format`, the script will:

- Inject the referenced snippet into the code block. **Note:** Existing code block content will be overwritten - don’t iterate on your code in an MDX file, or you’ll lose it!
- Remove extra whitespace between the ends of the snippet
- If `startafter` and `endbefore` properties were provided, only the code between them will be injected

### Callouts

Callouts are useful for calling attention to small chunks of content. There are currently two types of callout components you can use: `Note` and `Warning`.

`Note` is suitable for calling attention to info that is helpful or important but will not result in something breaking if ignored. For example, indicating a page is specific to Dagster Cloud.

```markdown
<Note>
    Content goes here. <strong>Any formatting must be done with HTML.</strong>
</Note>
```

Unlike `Note`, `Warning` should be used sparingly and only when absolutely necessary. `Warning` is meant to convey a sense of urgency, highlighting information that the user must be aware of or they’ll have a bad time. For example, changing a setting in prod without testing.

```markdown
<Warning>
    <strong>Don't</strong> pizza when you should french fry!
</Warning>
```

### Article list

The `ArticleList` component creates two-column list of links, which is useful for displaying long link lists in a more tidy fashion. The `ArticleList` component accepts child `ArticleListItem` components, where each item is an individual link. For example:

```markdown
<ArticleList>
  <ArticleListItem
    title="External link example"
    href="/guides/dagster/example_project"
  ></ArticleListItem>
  <ArticleListItem
    title="Relative link example"
    href="/getting-started"
  ></ArticleListItem>
</ArticleList>
```

The `ArticleListItem` component accepts the following properties, **all of which are required**:

- `title` - The display text for the link
- `href` - A relative or external URL. Anchor links (`#some-heading`) are also acceptable.

### Tabs

The `TabGroup` component creates a tabbed interface, which is useful for condensing the display of lengthy content. It’s generally recommended to use tabs when presenting content that is “either-or”, **not sequential**. For example, different ways to load a code location using the `dagster` CLI.

The `TabGroup` component accepts child `TabItem` components, where each item is a tab. For example:

```markdown
## Loading code locations locally

<TabGroup>
    <TabItem name="Some content">
    ... some content ...
    </TabItem> 
    <TabItem name="More content">
  ... some more content ...
    </TabItem> 
    <TabItem name="Markdown content">

**Markdown content is supported**...

But must be flush-left **and** have beginning and ending new lines to render correctly.

</TabGroup>
```

### API docs

#### General

<details><summary><strong>Relevant CLI commands</strong></summary>

| Command | Run location | Usage | Description |
| --- | --- | --- | --- |
| make apidoc-build | /docs | Local API docs dev |  |
| make apidoc-watch-build | /docs | Local API docs dev |  |

</details>

The API docs contain the formal specification of Dagster’s APIs. These docs are built with [Sphinx](https://www.sphinx-doc.org/en/master/) and its [autodoc extension](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html), which we use to document Python methods and classes by parsing docstrings in the Dagster codebase.

Updates to API docs are made to the `.rst` files in `/sphinx`. Each Dagster concept and library has its own `.rst` file. While there is some copy in these files, their main purpose is to invoke `autodoc` directives. These directives pull in docstrings from the Dagster codebase, which Sphinx uses to generate the corresponding API documentation. The end result are the JSON files in `/content/api`.

If you make updates to `.rst` files in `/sphinx`, you’ll need to rebuild the API docs to have your changes reflected on the docs site. Refer to the [Building the API docs section](#building-the-api-docs) for more info.

### Formatting in reStructuredText

While formatting in `.rst` (reStructuredText) files is similar to Markdown, there are some differences. Refer to the [reStructuredText formatting reference][reference-markdown-rst] for examples of commonly used formats, including bold, italics, code, and links.

### Building the API docs

If you make changes to any `.rst` files in `/sphinx`, you’ll need to rebuild the API docs to have your changes reflected on the docs site. This is enforced by CI, which both verifies that the docs built successfully and that the build output matches what’s checked into the `dagster-io/dagster` repository. This prevents merging docs source changes without the corresponding build.

The overall build process looks like the following, which is described in more detail following the diagram:

![API docs workflow](/next/public/images/readme/api-docs-workflow.png)

1. Python docstrings are added to the Dagster codebase. While not all updates to the API docs will include this step, we’re including it for completeness.
2. Updates are made to `.rst` files in `/sphinx`.
3. You run one of the following:
    1. `make apidoc-build` - This command executes the Sphinx build step.
    2. `make apidoc-watch-build` - This command is identical to `make apidoc-build`, but also starts the `watchmedo` file watcher. Every time an `.rst` file or the Sphinx configuration file is modified, `watchmedo` will automatically re-run `make apidoc-build`. If the build finishes successfully, NextJS will auto-reload your local docs server.
4.  Using the `sphinx` tox environment (`tox.ini`), Sphinx extracts docstrings from the Dagster codebase using `autodoc` directives in `.rst` files to build JSON (`/sphinx/_build/json`).
5. Next, the `/scripts/pack_json.py` script is run. This script does two things:
    1. Transforms the Sphinx JSON into a NextJS-friendly format
    2. Writes the transformed JSON to `/content/api`, with the final output being three JSON files:
        1. `modules.json` - Used to render individual API pages. Each page corresponds to a single `.rst` source file.
        2. `searchindex.json` - Used to power the [`PyObject`][component-pyobject] component
        3. `sections.json` - Used to render `/content/_apidocs.mdx`

### Mocking runtime dependencies

The Python environment in which Sphinx runs requires all targeted modules to be available on `sys.path`. This is because `autodoc` actually imports the modules during build, to access their docstrings. This means the Sphinx build process also imports anything else imported in the targeted modules. Thus, Sphinx requires the entire graph of imports discoverable from your targets to be available on `sys.path`.

The simplest way to achieve this is to install all of the target packages with `pip` into the Sphinx build environment, just as you would for a runtime environment. The problem is that, not all the packages you are targeting in the build can necessarily be installed into the same environment. That's often the case with our API docs: a single run of Sphinx builds the API docs for all Dagster packages and some of those extensions can have conflicting requirements.

However, the `autodoc_mock_imports` configuration option in `autodoc` can help in this scenario. Every package listed in `autodoc_mock_imports` will be mocked during the Sphinx build, meaning that all imports from that package will return fake objects. **Note:** `autodoc_mock_imports` shadows the actual build environment. For example, if you have `foo` installed in the environment but `foo` is also listed in `autodoc_mock_imports`, imports will return mocks.

Ideally, we’d be able to put all build target (Dagster packages) dependencies in `autodoc_mock_imports`, but this isn’t a foolproof solution. If a dependency is used at import time and it’s mocked, a Python error will occur during the Sphinx build. This is because your code will encounter a mocked object where it expects a different value from the library. 

For example, this is likely to crash the build because the value of `SOME_CONSTANT` is actually being used at import time:

```
from some_mocked_lib import SOME_CONSTANT

do_something(SOME_CONSTANT)
```

If `SOME_CONSTANT` were merely imported, then mocking `some_mocked_lib` would work.

The solution used for our Sphinx environment is a compromise: Any Dagster package that uses any dependencies at build time is a full editable install, and all other dependencies are mocked. Refer to  `autodoc_mock_imports` in `/docs/sphinx/conf.py` for more info.

While not ideal for having a lean build environment, as it brings in all other dependencies of a Dagster package even if only one is used at import time -n it keeps the build environment simple. A more targeted approach would be cherrypicking assorted dependencies and keeping their version specifiers in sync with the corresponding Dagster package.

### Site navigation

The site navigation, which specifies the contents of the left sidebar, is maintained in [`/content/_navigation.json`][docs-navigation-source]. For example:

https://github.com/dagster-io/dagster/blob/b2b5f563069d476f519da5f188b47ba14c014495/content/_navigation.json#L2-L25

Generally, you should update the navigation when:

- An MDX file is added or removed
- An MDX file is moved to a new location
- An API doc is added or removed
- The title of a page substantially changes

### Redirects

Redirects are maintained in [`/next/util/redirectUrls.json`][docs-redirect-source]. Each entry contains a `source`, `destination`, and a `statusCode`. For example:

https://github.com/dagster-io/dagster/blob/7854e62f861a80acbf3d093f3a614057c910c0f4/docs/next/util/redirectUrls.json#L2-L6

When a visitor navigates to the `source` URL, they’ll automatically be redirected to the `destination` URL.

Generally, you should add a redirect when:

- An MDX file is moved to a new location
- An MDX file is consolidated with another MDX file

---

## Releasing and versioning

The docs are updated with every release, which is currently weekly on Thursday. [docs.dagster.io/master](http://docs.dagster.io/master) is updated on every commit to `dagster-io/dagster`'s `master` branch.

The difference is because the docs use a custom versioning logic to account for differences in Dagster versions:

- The `master` version points to files in `/content`
- Older versions render MDX files and images from a remote Amazon S3 bucket

During every release, the newly-released content is uploaded to the S3 bucket. This results in the latest version of the docs (`docs.dagster.io`) updating on every release as opposed to every `master` push.

---

## Useful tools

### Automating screenshots with dagit-screenshot

Screenshots are image files living in `/next/public/images`, typically under a subdirectory corresponding to the page on which they appear. There's no need to manually manage the screenshots in this directory-- instead you can add a specification your screenshot to `screenshots` and run `dagit-screenshot capture` to quasi-automatically generate the screenshot and place it in the appropriate subdirectory of `next/public/images`.

All non-remotely-sourced images should be stored in `next/public/images`. This directory is organized in a hierarchy that matches the structure of the prose docs, which keeps clear which images are used in which docs. For instance, images used in the `concepts/ops-jobs-graphs` pages are typically stored in `images/concepts/ops-jobs-graphs`.

Most of the site's images are screenshots of the Dagster UI. There is a semi-automated system in place to ease the generation and maintenance of screenshots. Screenshots are specified in "specs" which are stored in YAML files in the `screenshots` directory. This directory contains a "screenshot spec database", which is just a tree of YAML files that matches the hierarchical structure of `content`. These files are intended to be read by the command-line tool `dagster-ui-screenshot`, which generates and writes screenshot image files to `next/public/images`. See `dagster-ui-screenshot/README.md` for details.

---

## References

- [Markdown and reStructuredText formatting][reference-markdown-rst]
- [CLI commands][reference-cli-commands]

### Markdown and reStructuredText formatting

The following table includes the most commonly-used formats in Markdown and reStructuredText (`.rst` files, used for API documentation). Refer to the official documentation for either language for full references: [Markdown](https://daringfireball.net/projects/markdown/syntax), [Sphinx](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html)

<table>
<thead>
  <tr>
    <th>Description</th>
    <th>Markdown</th>
    <th>reStructuredText</th>
  </tr>
</thead>
<tbody>
  <tr>
<td>

[Italics](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#inline-markup)    

</td>
<td>
    
`_Text_`

</td>
<td>
    
`*Text*`

</td>
  </tr>
  <tr>
<td>
    
[Bold](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#inline-markup)

</td>
<td>
    
`**Text**`

</td>
<td>
    
`**Text**`

</td>
  </tr>
  <tr>
<td>
    
[Code (inline)](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#inline-markup)

</td>
<td>
    
    `Text`

</td>
<td>
    
    `Text`

</td>
  </tr>
  <tr>
<tr>
<td>
Code block
</td>
<td>

````
```language
```
````

</td>
<td>
</td>
</tr>
<td>Link (relative)</td>
<td>
    
`[Link text](/path/to/page)`

</td>
<td>
    
```
`Link text </path/to/page>`_
```

</td>
  </tr>
  <tr>
<td>Link (external)
</td>
<td>
    
`[Link text](https://some-link.com)`

</td>
<td>
    
```
`Link text <https://some-link.com>`_
```

</td>
  </tr>
  <tr>
<td>List (bullet)</td>
<td>
    
```
- one
- two
   - nested list
   - nested list 2
- three
```

</td>
<td>
    
```
* one
* two

   * nested list
   * nested list 2

* three
```

</td>
  </tr>
  <tr>
<td>List (numbered)</td>
<td>
    
```
1. one
2. two
```

</td>
<td>
    
```
1. one
2. two
```

Or

```
#. one
#. two
```

</td>
  </tr>
<td>

Quote

</td>
<td>

```
> Text text text
```

</td>
<td>

```
> Text text text
```

</td>
</tbody>
</table>

### CLI commands

| Command | Run location | Usage | Description |
| :--- | :--- | :--- | :--- |
| make next-dev-install | /docs | Local setup | Sets up the site's environment. Only required during initial setup and installation. |
| make next-watch-build | /docs | Local dev | Runs the development server on `localhost:3001`. Watches MDX files in `/content` and site code in `/next`. |
| make mdx-format | /docs | Content | Runs [/docs/next/scripts/mdx-transform.ts][mdx-format-source], which formats MDX and React code. This includes standardizing MDX content, inserting code snippet content into code blocks, transforming HTML img/ Markdown images into Image components. Run immediately prior to committing changes to prevent a Buildkite error.<br><br>**Note**: If you’ve edited code snippets, you should run `make black isort` before running this and committing changes. Our CI checks the contents of code snippets in MDX against their source files and fails if there’s a mismatch. If running `black` and `isort` does make changes to your code snippets, running `mdx-format` last ensures that there won’t be a mistmatch due to formatting. |
| make black | / | Code snippets | Runs Black, a code formatting CLI utility. Invokes `black` in `/Makefile`<br>If you've added or editing code snippets, run prior to running `make mdx-format`. Refer to the [Development section][docs-development] for more info. |
| make isort | / | Code snippets | Runs `isort`, a Python code formatting utility. Invokes `isort` in `/Makefile`<br>If you've added or editing code snippets, run prior to running `make mdx-format`. Refer to the [Development section][docs-development] for more info. |
| pytest <path_to_file>.py |  | Code snippets | Runs `pytest` against the provided Python file. Used to test code snippets. |
| yarn test | /docs/next | Content | Runs [internal test scripts][link-tests], which tests the validity of internal and external links. |
| make apidoc-buildsphinx |  | API docs |  |
| make apidoc-watch-build |  | API docs |  |
| sphinx build |  | API docs |  |

---

## Dagster University

Refer to the Dagster University [README](https://github.com/dagster-io/dagster/tree/master/docs/dagster-university) for more info about working in this directory.

---

## Troubleshooting

- [Error: ModuleNotFoundError: No module named 'X']

### Error: ModuleNotFoundError: No module named 'X'

Related to the [API docs][api-docs].

The following error occurs after a new library is added as a dependency in a Dagster package. It could have been done by your or in another commit. The issue is that the library isn't present in your `tox` environment.

Example stack trace:

```
dagster/docs $ make apidoc-build
...

/Users/jamie/dev/dagster/docs/sphinx/sections/api/apidocs/cli.rst:60: ERROR: Failed to import "grpc_command" from "dagster._cli.api". The following exception was raised:
Traceback (most recent call last):
File "/Users/jamie/dev/dagster/docs/.tox/sphinx/lib/python3.9/site-packages/sphinx_click/ext.py", line 403, in _load_module
    mod = __import__(module_name, globals(), locals(), [attr_name])
File "/Users/jamie/dev/dagster/python_modules/dagster/dagster/_cli/__init__.py", line 8, in <module>
    from .api import api_cli
File "/Users/jamie/dev/dagster/python_modules/dagster/dagster/_cli/api.py", line 14, in <module>
    from dagster._cli.workspace.cli_target import (
File "/Users/jamie/dev/dagster/python_modules/dagster/dagster/_cli/workspace/__init__.py", line 1, in <module>
    from .cli_target import get_workspace_process_context_from_kwargs, workspace_target_argument
File "/Users/jamie/dev/dagster/python_modules/dagster/dagster/_cli/workspace/cli_target.py", line 7, in <module>
    import tomli
ModuleNotFoundError: No module named 'tomli'
```

To resolve the error, you need to rebuild your `tox` environment and bring in the missing dependency. To do this:

- To rebuild the environment for every `tox` command, run the following in `/docs`:

   ```shell
   tox -r
   ```

- To rebuild and run only the Sphinx command, run the following in `/docs`:

   ```
   tox -re sphinx
   ```
   

<!-- ## CONTENT -->

[docs-content]: #general-mdx-content
[docs-content-source]: https://github.com/dagster-io/dagster/tree/master/docs/content

[docs-navigation]: #site-navigation
[docs-navigation-source]: https://github.com/dagster-io/dagster/blob/master/docs/content/_navigation.json

[docs-redirect]: #redirects
[docs-redirect-source]: https://github.com/dagster-io/dagster/blob/master/docs/next/util/redirectUrls.json

[docs-development]: #development
[docs-development-local]: #local
[docs-pull-requests]: #pull-requests

[docs-page-architecture]: #page-architecture
[docs-site-structure]: #directory-structure

[docs-code-snippets]: #code-snippets
[docs-site-technologies]: #site-technologies

<!-- ## API -->

[api-docs]: #api-docs
[api-apidocs-source]: https://github.com/dagster-io/dagster/blob/master/docs/content/_apidocs.mdx
[api-folder]: https://github.com/dagster-io/dagster/tree/master/docs/content/api

<!-- [api-sphinx]: -->
[api-sphinx-source]: https://github.com/dagster-io/dagster/tree/master/docs/sphinx

<!-- ## NEXT -->

<!-- [mdx-format]:  -->
[mdx-format-source]: https://github.com/dagster-io/dagster/blob/master/docs/next/scripts/mdx-transform.ts

[next-folder]: https://github.com/dagster-io/dagster/tree/master/docs/next
[next-assets]: https://github.com/dagster-io/dagster/tree/master/docs/next/public

[next-images]: #images
[next-images-source]: https://github.com/dagster-io/dagster/tree/master/docs/next/public/images

[next-components]: #page-elements-components
[next-components-source]: https://github.com/dagster-io/dagster/blob/master/docs/next/components/mdx/MDXComponents.tsx

[component-article-list]: #article-list
[component-callout]: #callouts
[component-code-snippet]: #code-snippets
[component-image]: #images
[component-pyobject]: #pyobject
[component-tab]: #tabs

[next-page-tsx]: https://github.com/dagster-io/dagster/blob/master/docs/next/pages/%5B...page%5D.tsx
[next-versioned-content]: https://github.com/dagster-io/dagster/tree/master/docs/next/.versioned_content

[link-tests]: https://github.com/dagster-io/dagster/tree/master/docs/next/__tests__

<!-- ## DAGIT SCREENSHOT -->

<!-- [dagit-screenshot]:  -->
[dagit-screenshot-source]: https://github.com/dagster-io/dagster/tree/master/docs/dagit-screenshot
[dagit-screenshot-config]: https://github.com/dagster-io/dagster/tree/master/docs/screenshots

<!-- ## REFERENCES -->

[reference-cli-commands]: #cli-commands
[reference-markdown-rst]: #markdown-and-restructuredtext-formatting