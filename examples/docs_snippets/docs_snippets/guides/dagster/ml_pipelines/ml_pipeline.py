# ruff: isort: skip_file

## data_ingestion_start
import requests
from dagster import asset
import pandas as pd


@asset
def hackernews_stories():
    # Get the max ID number from hacker news
    latest_item = requests.get(
        "https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()
    # Get items based on story ids from the HackerNews items endpoint
    results = []
    scope = range(latest_item - 1000, latest_item)
    for item_id in scope:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)
    # Store the results in a dataframe and filter on stories with valid titles
    df = pd.DataFrame(results)
    if len(df) > 0:
        df = df[df.type == "story"]
        df = df[~df.title.isna()]

    return df


## data_ingestion_end

## test_train_split_start

from sklearn.model_selection import train_test_split
from dagster import multi_asset, AssetOut


@multi_asset(outs={"training_data": AssetOut(), "test_data": AssetOut()})
def training_test_data(hackernews_stories):
    hackernews_stories = hackernews_stories
    X = hackernews_stories.title
    y = hackernews_stories.descendants
    # Split the dataset to reserve 20% of records as the test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train, y_train), (X_test, y_test)


## test_train_split_end


## vectorizer_start
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


@multi_asset(
    outs={"tfidf_vectorizer": AssetOut(), "transformed_training_data": AssetOut()}
)
def transformed_train_data(training_data):
    X_train, y_train = training_data
    # Initiate and fit the tokenizer on the training data and transform the training dataset
    vectorizer = TfidfVectorizer()
    transformed_X_train = vectorizer.fit_transform(X_train)
    transformed_X_train = transformed_X_train.toarray()
    y_train = y_train.fillna(0)
    transformed_y_train = np.array(y_train)
    return vectorizer, (transformed_X_train, transformed_y_train)


@asset
def transformed_test_data(test_data, tfidf_vectorizer):
    X_test, y_test = test_data
    # Use the fitted tokenizer to transform the test dataset
    transformed_X_test = tfidf_vectorizer.transform(X_test)
    transformed_y_test = np.array(y_test)
    y_test = y_test.fillna(0)
    transformed_y_test = np.array(y_test)
    return transformed_X_test, transformed_y_test


## vectorizer_end


## models_start

import xgboost as xg
from sklearn.metrics import mean_absolute_error


@asset
def xgboost_comments_model(transformed_training_data):
    transformed_X_train, transformed_y_train = transformed_training_data
    # Train XGBoost model, which is a highly efficient and flexible model
    xgb_r = xg.XGBRegressor(
        objective="reg:squarederror", eval_metric=mean_absolute_error, n_estimators=20
    )
    xgb_r.fit(transformed_X_train, transformed_y_train)
    return xgb_r


@asset
def comments_model_test_set_r_squared(transformed_test_data, xgboost_comments_model):
    transformed_X_test, transformed_y_test = transformed_test_data
    # Use the test set data to get a score of the XGBoost model
    score = xgboost_comments_model.score(transformed_X_test, transformed_y_test)
    return score


## models_end


## inference_start
@asset
def latest_story_comment_predictions(xgboost_comments_model, tfidf_vectorizer):
    # Get the max ID number from hacker news
    latest_item = requests.get(
        "https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()
    # Get items based on story ids from the HackerNews items endpoint
    results = []
    scope = range(latest_item - 100, latest_item)
    for item_id in scope:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

    df = pd.DataFrame(results)
    if len(df) > 0:
        df = df[df.type == "story"]
        df = df[~df.title.isna()]
    inference_x = df.title
    # Transform the new story titles using the existing vectorizer
    inference_x = tfidf_vectorizer.transform(inference_x)
    return xgboost_comments_model.predict(inference_x)


## inference_end
