# machine_learning_example

This is an example of how to use Dagster for machine learning. A full guide on [how to build machine learning pipelines with Dagster](https://docs.dagster.io/guides/dagster/ml-pipeline) can be used along with this example. 

## Getting started

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

In this example, we use the Hacker News titles to predict the number of comments on a story. 

Benefits of using Dagster for Machine Learning :
- Dagster makes iterating on machine learning models and testing easy, and it is designed to use during the development process.
- Dagster has a lightweight execution model means you can access the benefits of an orchestrator, like re-executing from the middle of a pipeline and parallelizing steps while you're experimenting.
- Dagster models data assets, not just tasks, so it understands the upstream and downstream data dependencies.
- Dagster is a one-stop shop for both the data transformations and the models that depend on the data transformations.