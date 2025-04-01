---
title: "Building machine learning pipelines with Dagster"
description: This guide illustrates how to use Dagster to operationalize your machine learning pipeline
---

In this guide, we’ll walk you through how to take your machine learning models and deploy and maintain them in production using Dagster, reliably and efficiently.

We will work through building a machine learning pipeline, including using assets for different elements, how to automate model training, and monitoring your model's drift.


## Before you begin

This guide assumes you have familiarity with machine learning concepts and several Dagster concepts, including [asset definitions](/guides/build/assets/defining-assets) and [jobs](/guides/build/jobs).


## Benefits of building machine learning pipelines in Dagster

- Dagster makes iterating on machine learning models and testing easy, and it is designed to use during the development process.
- Dagster has a lightweight execution model means you can access the benefits of an orchestrator, like re-executing from the middle of a pipeline and parallelizing steps while you're experimenting.
- Dagster models data assets, not just tasks, so it understands the upstream and downstream data dependencies.
- Dagster is a one-stop shop for both the data transformations and the models that depend on the data transformations.

## Machine learning development

If you are already using Dagster for your ETL pipelines, it is a natural progression to build out and test your models in Dagster.

For this guide, we will be using Hacker News data. The machine learning model we will walk through takes the Hacker News stories and uses the titles to predict the number of comments that a story will generate. This will be a supervised model since we have the number of comments for all the previous stories.

The assets graph will look like this at the end of this guide (click to expand):

![ML asset DAG](/images/guides/build/ml-pipelines/ml-pipeline/ml_asset_dag.png)

### Ingesting data

First, we will create an asset that retrieves the most recent Hacker News records.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" startAfter="data_ingestion_start" endBefore="data_ingestion_end" />

### Transforming data

Now that we have a dataframe with all valid stories, we want to transform that data into something our machine learning model will be able to use.

The first step is taking the dataframe and splitting it into a [training and test set](https://en.wikipedia.org/wiki/Training,\_validation,\_and_test_data_sets). In some of your models, you also might choose to have an additional split for a validation set. The reason we split the data is so that we can have a test and/or a validation dataset that is independent of the training set. We can then use that dataset to see how well our model did.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" startAfter="test_train_split_start" endBefore="test_train_split_end" />

Next, we will take both the training and test data subsets and [tokenize the titles](https://en.wikipedia.org/wiki/Lexical_analysis) e.g. take the words and turn them into columns with the frequency of terms for each record to create [features](https://en.wikipedia.org/wiki/Feature_\(machine_learning\)) for the data. To do this, we will be using the training set to fit the tokenizer. In this case, we are using [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) and then transforming both the training and test set based on that tokenizer.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" startAfter="vectorizer_start" endBefore="vectorizer_end" />

We also transformed the dataframes into NumPy arrays and removed `nan` values to prepare the data for training.

### Training the model

At this point, we have `X_train`, `y_train`, `X_test`, and `y_test` ready to go for our model. To train our model, we can use any number of models from libraries like [sklearn](https://scikit-learn.org/), [TensorFlow](https://www.tensorflow.org/), and [PyTorch](https://pytorch.org/).

In our example, we will train an [XGBoost model](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor) to predict a numerical value.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" startAfter="models_start" endBefore="models_end" />

### Evaluating our results

In our model assets, we evaluated each of the models on the test data and in this case, got the [score](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor.score) derived from comparing the predicted to actual results. Next, to predict the results, we'll create another asset that runs inference on the model more frequently than the model is re-trained.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" startAfter="inference_start" endBefore="inference_end" />

Depending on what the objective of your ML model is, you can use this data to set alerts, save model performance history, and trigger retraining.

## Where to go from here

- [Managing machine learning models with Dagster](/guides/build/ml-pipelines/managing-ml) - This guide reviews ways to manage and maintain your machine learning (ML) models in Dagster
- Dagster integrates with [MLflow](/api/python-api/libraries/dagster-mlflow) that can be used to keep track of your models
- Dagster integrates with [Weights & Biases](/api/python-api/libraries/dagster-wandb). For an example that demonstrates how to use W\&B's artifacts with Dagster, see the [Dagster repository](https://github.com/dagster-io/dagster/tree/master/examples/with_wandb).
