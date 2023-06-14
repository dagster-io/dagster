# Basic Machine Learning Example with Assets

This is an example of how to use Dagster for machine learning. A full guide on [how to build machine learning pipelines with Dagster](https://docs.dagster.io/guides/dagster/ml-pipeline) can be used along with this example. 

## Getting started

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

In this example, we use the Hacker News API, a popular news aggregation website [Hacker News](https://news.ycombinator.com/) to get data on the latest stories and use their titles to predict the number of comments on a story. 

Benefits of using Dagster for machine learning:
- You can iterate on models and testing easily, Dagster helps you transition from development to production.
- Access the benefits of an orchestrator, like re-executing from the middle of a pipeline and parallelizing steps while you're experimenting.
- Consolidate your data transformations and machine learning models in a single platform