# Documentation style guide

## Dagster approach to documentation style

We will build out our own approach over time, but for now, we roughly follow the [GitHub Docs approach to style](https://docs.github.com/en/contributing/style-guide-and-content-model/style-guide#the-github-docs-approach-to-style) and the [GitHub Docs voice and tone guidelines](https://docs.github.com/en/contributing/style-guide-and-content-model/style-guide#voice-and-tone).

### General guidelines

- Use the active voice as much as possible. Sometimes you may need to use the passive voice when the object that is being acted on is the focus of the sentence.
- Avoid superlatives like `very`, `easy`, `extremely`, and `simply` .
- See the [Dagster docs contributing guidelines](https://github.com/dagster-io/dagster/blob/master/docs/CONTRIBUTING.md) for information on code example formatting, custom and built-in Docusaurus components, and more.

## Acronyms and abbreviations

- **Always define acronyms and abbreviations before using them,** even if they're well-known. The definition should be the first instance of the acronym in the content. After it's defined, it can be used instead of the full name, e.g.  ****`Amazon Web Services (AWS) supports Redshift. AWS has a free tier.`
- Include the brand or provider's name when first naming a product, feature, or service. Any time thereafter in the same page, just the product, feature, or service name can be used, e.g. `Amazon S3`, and then `S3` thereafter.

## Diagrams and flowcharts

- Source file for [draw.io](http://draw.io) component library: [https://drive.google.com/file/d/1FGDdKmNms7CMaNrwJx8JOzE_wv8h_csJ/view?usp=sharing](https://drive.google.com/file/d/1FGDdKmNms7CMaNrwJx8JOzE_wv8h_csJ/view?usp=sharing)
- Library file for loading into draw.io: [https://drive.google.com/file/d/1omCVzoNhi2aLYL2bWbiT4-r3TLvsobMa/view?usp=sharing](https://drive.google.com/file/d/1omCVzoNhi2aLYL2bWbiT4-r3TLvsobMa/view?usp=sharing)

## Images and screenshots

- In general, try to minimize the use of screenshots, since they are hard to maintain.
- Image names must be hyphen-separated for SEO. (This is also true for file and path names.)
- Include [alt text](https://webaim.org/techniques/alttext/) on all screenshots.
- For recommended image resolution and the location of screenshot files and other static assets, see the [CONTRIBUTING guide](https://github.com/dagster-io/dagster/blob/master/docs/CONTRIBUTING.md#images).

## Links

- Link to other docs (especially API docs) where relevant. For guidance on formatting API docs links with the `PyObject` component, see the [CONTRIBUTING guide](https://github.com/dagster-io/dagster/blob/master/docs/CONTRIBUTING.md#linking-to-api-docs-with-pyobject).
- When linking to other docs, put the link at the end of the sentence. For an example, see the first item in this list.
- In general, try to follow [web accessibility best practices](https://webaim.org/techniques/hypertext/link_text) for links:
    - **Avoid uninformative link phrases**, like "click here", "more", "read more". Whenever possible, use the full page name when linking to another doc, e.g. `For more information, see [Testing sensors](https://docs.dagster.io/guides/automate/sensors/testing-sensors)`

## Lists

- Use ordered lists only when the order of items matters (for example, when listing steps in a procedure).
- Use unordered lists when the order of items doesn't matter.

## Procedural steps

- Use numbered steps for procedures.
- Each step should describe an action the user can take, for example, "Click **Materialize all**". Steps can be marked as optional in parentheses: "(Optional) Click **Materialize all**".
- In general, when writing procedural steps, it is best to describe the outcome of an action, then describe the action(s) needed to achieve it. For example: "To sign in, enter your username and password, then click **Sign in**". This keeps the focus on the task the user is trying to complete, not the intricacies of the UI or implementation details of the code needed to complete the task.

## Terminology

- The names of programming languages (`Python`, `Rust`) should follow the official style guidelines for that language.

### **Key terms and definitions**

| **Term** | **Definition** | **Notes** | **Formatting** |
| --- | --- | --- | --- |
| Asset | An **asset** is an object in persistent storage, such as a table, file, or persisted machine learning model. |  |  |
| Asset graph | Refers to the Asset graph in the Dagster UI, accessed via the **View global lineage** link. |  |  |
| Asset materialization | An event indicating that an op has materialized an asset. |  |  |
| Asset observation | An event that records metadata about a given asset. Unlike asset materializations, asset observations do not signify that an asset has been mutated. |  |  |
| Backfill |  |  |  |
| Branch deployments | A Dagster-specific term, a branch deployment automatically creates a staging environment of Dagster code in a Dagster Cloud instance. |  |  |
| CLI | An acronym for **command line interface.**  |  |  |
| Code location | A collection of Dagster code definitions, accessible from a Python file or module, that are loaded by Dagster tools. |  |  |
| Component |  |  |  |
| Config |  |  |  |
| Configuration |  |  |  |
| DAG | An acronym for **directed acylic graph.** | Use this term explicitly when referring to the graph itself, and not in a generic way to refer to a pipeline.

Not interchangeable with "Asset graph". |  |
| Dagster+ | The name of Dagster's cloud-based deployment offering. |  |  |
| Dagster daemon |  |  |  |
| Dagster instance |  |  |  |
| Declarative automation |  |  |  |
| Definition(s) |  |  |  |
| Deployment |  |  |  |
| Graph |  |  |  |
| Graph-backed asset |  |  |  |
| Hybrid | The hosting configuration in Dagster+ in which a customer provides their own agent and has control over their own data plane. |  |  |
| I/O manager | User-provided objects that store asset and op outputs and load them as inputs to downstream assets/ops. |  |  |
| Integration |  |  |  |
| Job |  |  |  |
| Materialize / Materialization | To execute an operation that will produce an asset. |  |  |
| Multi-asset | A multi-asset represents a set of software-defined assets that are all updated by the same op or graph. |  |  |
| Op |  |  |  |
| Partition |  |  |  |
| Pipeline | A predefined set of steps and all the components required to complete a move and transformation of data for a given task.  |  |  |
| Platform | The tools, infrastructure, and code customers build to run their internal data projects. | Dagster is the **control plane for a company's data platform**. We are not the platform. |  |
| Project |  |  |  |
| Run | A single instance of the execution of a job. |  |  |
| Run coordinator |  |  |  |
| Run launcher |  |  |  |
| Run monitoring |  |  |  |
| Run retry |  |  |  |
| Schedule |  |  |  |
| Secret |  |  |  |
| Sensor |  |  |  |
| Serverless | The hosting configuration in Dagster+ in which Dagster manages both the control and data planes for a client. |  |  |
| Software-defined asset | A **Software-defined asset** is a Dagster object that couples an asset to the function and upstream assets that are used to produce its contents. |  |  |

## Titles and headings

- Use sentence case for titles and headings. For example, `Building pipelines with Databricks`, `Metadata and tags`.
- The H1 for the page is inherited from the title, so you don't need to include it, unless it differs from the title. In general, try not to have these different, since that's confusing for readers.

## UI components

- When referring to buttons, links, and other UI components that contain copy, the reference in docs should exactly match what's in the UI. This includes capitalization.
- Format text for UI components and labels in bold, for example `The **Asset Catalog**`
- Buttons are clicked, not hit, pressed, or pushed.