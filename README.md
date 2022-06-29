<p align="center">
<a href="https://dagster.io/"><img src="assets/dagster-logo.png"></a>
<br /><br />
<a href="https://twitter.com/dagsterio"><img src="https://img.shields.io/twitter/follow/dagsterio"></a>
<a href="https://dagster.io/slack"><img src="https://dagster-slackin.herokuapp.com/badge.svg"></a>
<a href="https://github.com/dagster-io/dagster"><img src="https://img.shields.io/github/stars/dagster-io/dagster?label=Star&style=social"></a>
</p>

# [Dagster](https://dagster.io/) &middot; [![GitHub license](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/dagster-io/dagster/blob/master/LICENSE) [![PyPI Version](https://badge.fury.io/py/dagster.svg)](https://pypi.org/project/dagster/) [![Coveralls coverage](https://coveralls.io/repos/github/dagster-io/dagster/badge.svg?branch=master)](https://coveralls.io/github/dagster-io/dagster?branch=master)

Dagster is an orchestration platform for the development, production, and observation of data assets.

- **Develop and test locally, then deploy anywhere:** With Dagster, the same computations can run
in-process against your local file system or on a distributed work queue against your production
data lake. Choose to locally develop on your laptop, deploy on-premise, or run in any
cloud.
- **Model the data produced and consumed:** In your orchestration graph, Dagster models data
dependencies and handles how data passes between steps. Gradual typing on inputs and outputs catches
bugs early.
- **Link data to computations:** Dagster’s Asset Catalog tracks the data sets and ML models produced
by your jobs. Understand how they were generated and trace issues when asset declarations
do not match their materializations in storage.
- **Build a self-service data platform:** Dagster helps platform teams build systems for data
practitioners. Jobs are built from shared, reusable, configurable data processing components.
Dagit, Dagster’s web interface, lets anyone inspect these objects and discover how to use them.
- **Declare and isolate dependencies:** Dagster’s server model enables you to isolate codebases. Problems
in one job will not bring down the system or other jobs. Each job can have its own package
dependencies and Python version.
- **Debug jobs from a rich interface**: Dagit includes expansive facilities for understanding
the jobs it orchestrates. When inspecting a run of your job, you can query over logs, discover the
most time-consuming tasks via a Gantt chart, re-execute subsets of steps, and more.

## Installation

Dagster is available on PyPI and officially supports Python 3.6+.

```bash
$ pip install dagster dagit
```

This installs two modules:

- **Dagster**: The core programming model.
- **Dagit**: The web interface for developing and operating Dagster jobs. It includes a DAG browser,
a type-aware interface to launch runs, a live view for in-progress runs, a catalog to view your data
assets, and more.

For a quick overview, check out our [Getting Started](https://docs.dagster.io/getting-started) page.

## Documentation

You can find the Dagster documentation [on the website](https://docs.dagster.io).

We've divided up the documentation into several sections:

- [🌱 Tutorial](https://docs.dagster.io/tutorial/)
- [💡 Concepts](https://docs.dagster.io/concepts)
- [🚢 Deployment](https://docs.dagster.io/deployment)
- [🤝 Integrations](https://docs.dagster.io/integrations)
- [📖 Guides](https://docs.dagster.io/guides)

## Community

Connect with thousands of other data practitioners building with Dagster. Share knowledge, get help,
and contribute to the open-source project. To see featured material and upcoming events, check out
our [Dagster Community](https://dagster.io/community) page.

Join our community here:

- 🌟 [Star us on Github](https://github.com/dagster-io/dagster)
- 🐦 [Follow us on Twitter](https://twitter.com/dagsterio)
- 📺 [Subscribe to our YouTube channel](https://www.youtube.com/channel/UCfLnv9X8jyHTe6gJ4hVBo9Q)
- 📚 [Read our blog posts](https://dagster.io/blog)
- 👋 [Join us on Slack](https://dagster.io/slack)
- ✏️ [Start a Github Discussion](https://github.com/dagster-io/dagster/discussions)

## Contributing

For details on contributing or running the project for development, check out our [contributing
guide](https://docs.dagster.io/community/contributing/).

## License

Dagster is [Apache 2.0 licensed](https://github.com/dagster-io/dagster/blob/master/LICENSE).
