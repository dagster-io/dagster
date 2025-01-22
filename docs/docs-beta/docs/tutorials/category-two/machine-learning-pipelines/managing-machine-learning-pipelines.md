---
title: Managing machine learning pipelines with Dagster
description: This guide illustrates how to use Dagster to operationalize your machine learning pipeline
last_update:
  author: Dennis Hume
sidebar_position: 30
---

You might have thought about your data sources, feature sets, and the best model for your use case. Inevitably, you start thinking about how to make this process sustainable and operational and deploy it to production. You want to make the machine learning pipeline self-sufficient and have confidence that the model you built is performing the way you expect. Thinking about machine learning operations, or MLOps, is the process of making your model maintainable and repeatable for a production use case.

## Automating ML model maintenance

Whether you have a large or small model, Dagster can help automate data refreshes and model training based on your business needs.

Declarative Automation can be used to update a machine learning model when the upstream data is updated. This can be done by setting the `AutomationCondition` to `eager`, which means that our machine learning model asset will be refreshed anytime our data asset is updated.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="4" lineEnd="13"/>

Some machine learning models might be more cumbersome to retrain; it also might be less important to update them as soon as new data arrives. For this, the `on_cron` condition may be used, which will cause the asset to be updated on a given cron schedule, but only after all of its upstream dependencies have been updated.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="19" lineEnd="28"/>

## Monitoring

Integrating your machine learning models into Dagster allows you to see when the model and its data dependencies were refreshed, or when a refresh process has failed. By using Dagster to monitor performance changes and process failures on your ML model, it becomes possible to set up remediation paths, such as automated model retraining, that can help resolve issues like model drift.

In this example, the model is being evaluated against the previous model’s accuracy. If the model’s accuracy has improved, the model is returned for use in downstream steps, such as inference or deploying to production.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="35" lineEnd="73"/>

A sensor can be set up that triggers if an asset fails to materialize. Alerts can be customized and sent through e-mail or natively through Slack. In this example, a Slack message is sent anytime the `ml_job` fails.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="87" lineEnd="106"/>

## Enhancing the Dagster UI with metadata

Understanding the performance of your ML model is critical to both the model development process and production. Metadata can significantly enhance the usability of the Dagster UI to show what’s going on in a specific asset. Using metadata in Dagster is flexible, can be used for tracking evaluation metrics, and viewing the training accuracy progress over training iterations as a graph.

One of the easiest ways to utilize Dagster’s metadata is by using a dictionary to track different metrics that are relevant for an ML model.

Another way is to store relevant data for a single training iteration as a graph that you can view directly from the Dagster UI. In this example, a function is defined that uses data produced by a machine learning model to plot an evaluation metric as the model goes through the training process and render that in the Dagster UI.

Dagster’s <PyObject object="MetadataValue" /> types enable types such as tables, URLs, notebooks, Markdown, etc. In the following example, the Markdown metadata type is used to generate plots. Each plot will show a specific evaluation metric’s performance throughout each training iteration also known as an epoch during the training cycle.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="101" lineEnd="116"/>

In this example, a dictionary is used called `metadata` to store the Markdown plots and the score value in Dagster.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/managing_ml/managing_ml_code.py" language="python" lineStart="127" lineEnd="158"/>

In the Dagster UI, the `xgboost_comments_model` has the metadata rendered. Numerical values, such as the `score (mean_absolute_error)` will be logged and plotted for each materialization, which can be useful to understand the score over time for machine learning models.

![Managing ML UI](/images/tutorial/machine-learning-pipelines/managing-ml-ui.png)

The Markdown plots are also available to inspect the evaluation metrics during the training cycle by clicking on **\[Show Markdown]**:

![Plot UI](/images/tutorial/machine-learning-pipelines/plot-ui.png)

## Tracking model history

Viewing previous versions of a machine learning model can be useful to understand the evaluation history or referencing a model that was used for inference. Using Dagster will enable you to understand:

- What data was used to train the model
- When the model was refreshed
- The code version and ML model version was used to generate the predictions used for predicted values

In Dagster, each time an asset is materialized, the metadata and model are stored. Dagster registers the code version, data version and source data for each asset, so understanding what data was used to train a model is linked.

In the screenshot below, each materialization of `xgboost_comments_model` and the path for where each iteration of the model is stored.

![Assets Materialization](/images/tutorial/machine-learning-pipelines/assets-materilization.png)

Any plots generated through the asset's metadata can be viewed in the metadata section. In this example, the plots of `score (mean_absolute_error)` are available for analysis.

![Metadata Plot](/images/tutorial/machine-learning-pipelines/metadata-plot.png)