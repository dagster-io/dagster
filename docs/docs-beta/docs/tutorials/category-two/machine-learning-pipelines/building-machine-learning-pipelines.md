---
title: Building machine learning pipelines with Dagster
description: This guide illustrates how to use Dagster to operationalize your machine learning pipeline
last_update:
  author: Dennis Hume
sidebar_position: 20
---

First, we will create an asset that retrieves the most recent Hacker News records.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" language="python" lineStart="8" lineEnd="29"/>

## Transforming data

Now that we have a DataFrame with all valid stories, we want to transform that data into something our machine learning model will be able to use.

The first step is taking the DataFrame and splitting it into a [training and test set](https://en.wikipedia.org/wiki/Training,\_validation,\_and_test_data_sets). In some of your models, you also might choose to have an additional split for a validation set. The reason we split the data is so that we can have a test and/or a validation dataset that is independent of the training set. We can then use that dataset to see how well our model did.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" language="python" lineStart="35" lineEnd="46"/>

Next, we will take both the training and test data subsets and [tokenize the titles](https://en.wikipedia.org/wiki/Lexical_analysis) e.g. take the words and turn them into columns with the frequency of terms for each record to create [features](https://en.wikipedia.org/wiki/Feature_\(machine_learning\)) for the data. To do this, we will be using the training set to fit the tokenizer. In this case, we are using [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) and then transforming both the training and test set based on that tokenizer.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" language="python" lineStart="52" lineEnd="78"/>

We also transformed the DataFrames into NumPy arrays and removed `nan` values to prepare the data for training.

## Training the model

At this point, we have `X_train`, `y_train`, `X_test`, and `y_test` ready to go for our model. To train our model, we can use any number of models from libraries like [sklearn](https://scikit-learn.org/), [TensorFlow](https://www.tensorflow.org/), and [PyTorch](https://pytorch.org/).

In our example, we will train an [XGBoost model](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor) to predict a numerical value.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" language="python" lineStart="85" lineEnd="106"/>

## Evaluating our results

In our model assets, we evaluated each of the models on the test data and in this case, got the [score](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor.score) derived from comparing the predicted to actual results. Next, to predict the results, we'll create another asset that runs inference on the model more frequently than the model is re-trained.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/ml_pipelines/ml_pipeline.py" language="python" lineStart="112" lineEnd="135"/>

Depending on what the objective of your ML model is, you can use this data to set alerts, save model performance history, and trigger retraining.

## Next steps

- Continue this tutorial with [managing machine learning pipelines](managing-machine-learning-pipelines)