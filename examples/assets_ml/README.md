# Machine Learning Examples

These are examples of Machine Learning assets and shows how to build the Dagster's [Software-Defined Assets](https://docs.dagster.io/concepts/assets/software-defined-assets) for Machine Learning). 

Examples:
- Machine learning pipeline example
- Machine learning pipeline with Mlflow example 

View a guide for machine learning in the Dagster docs at [Building machine learning pipelines with Dagster](https://docs.dagster.io/guides/dagster/ml-pipeline).

## Getting started

You can run:

```
dagster dev -w workspace.yaml
```

to load both examples into the Dagster UI.

## Asset groups

It contains two asset groups:

- `ml_example`
  - A machine learning model using Hacker News data assets that predicts the number of comments based on a story's title
- `ml_example_mlflow`
  - The same machine learning model as `ml_example` with mlflow capabilities integrated 


