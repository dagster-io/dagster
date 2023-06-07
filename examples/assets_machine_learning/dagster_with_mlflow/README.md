# dagster_with_mlflow

This is an example based on the basic machine learning project using [Software-Defined Assets](https://docs.dagster.io/concepts/assets/software-defined-assets) for Machine Learning with MLflow.

## Getting started

```bash
pip install -e ".[dev]"
```

Then, start the Dagster UI web server:

```bash
dagster dev
```

In this example, we use the Hacker News titles to predict the number of comments on a story. With the MLflow integration, you will be able to track different machine learning experiments and register your models to be used for inference. 

Benefits of using Dagster with MLflow:
- Dagster will allow you to track the lineage between your data and iterations of machine learning models
- Automation with Dagster, you can programmatically run different experiments using schedules that update both your data and models, and sensors that can update a model or run experements based on other events. 
- Insight into your model training and evaluation with MLflow. MLflow has built-in integrations with many of the model libraries. 

Note: We are setting up the MLflow UI to run on a specific port to be able to integrate and use it with Dagster. You can change this port as needed. 