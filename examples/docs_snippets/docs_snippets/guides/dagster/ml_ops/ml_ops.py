import pandas as pd
import requests
import numpy as np
from dagster import (
    MetadataValue,
    Output,
    asset,
    Definitions,
    DynamicPartitionsDefinition,
    Output,
    FreshnessPolicy,
)
import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import linear_model


@asset
def previous_item():
    previous_item = requests.get(
        f"https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()
    return previous_item


## data_ingestion_start


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=10))
def hackernews_stories(previous_item):
    """Get the max ID number from hacker news"""

    latest_item = requests.get(
        f"https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()

    """Get items based on story ids from the HackerNews items endpoint"""
    results = []
    scope = range(previous_item, latest_item)
    for item_id in scope:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

    df = pd.DataFrame(results)
    if len(df) > 0:
        df = df[df.type == "story"]
        df = df[~df.title.isna()]

    return df, latest_item


## data_ingestion_end

## test_train_split_start


@asset
def test_train_split(hackernews_stories):
    hackernews_stories, max_item = hackernews_stories
    X = hackernews_stories.title
    y = hackernews_stories.descendants
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return X_train, X_test, y_train, y_test


## test_train_split_end


## vectorizer_start
@asset
def transform_train(test_train_split):
    X_train, X_test, y_train, y_test = test_train_split
    vectorizer = TfidfVectorizer()
    transformed_X_train = vectorizer.fit_transform(X_train)
    transformed_X_train = transformed_X_train.toarray()
    y_train = y_train.fillna(0)
    transformed_y_train = np.array(y_train)

    return vectorizer, transformed_X_train, transformed_y_train


@asset
def transform_test(test_train_split, transform_train):
    X_train, X_test, y_train, y_test = test_train_split
    vectorizer, transformed_X_train, transformed_y_train = transform_train
    transformed_X_test = vectorizer.transform(X_test)
    transformed_y_test = np.array(y_test)
    y_test = y_test.fillna(0)
    transformed_y_test = np.array(y_test)
    return transformed_X_test, transformed_y_test


## vectorizer_end

## models_start

from sklearn.tree import DecisionTreeRegressor


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=1440))
def decision_tree(transform_train, transform_test):
    vectorizer, transformed_X_train, transformed_y_train = transform_train
    decision_tree1 = DecisionTreeRegressor(max_depth=10)
    decision_tree1.fit(transformed_X_train, transformed_y_train)
    transformed_X_test, transformed_y_test = transform_test
    score = decision_tree1.score(transformed_X_test, transformed_y_test)
    return decision_tree1, decision_tree1.score(transformed_X_test, transformed_y_test)


import xgboost as xg
from sklearn.metrics import mean_absolute_error


@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=1440))
def xgboost(transform_train, transform_test):
    vectorizer, transformed_X_train, transformed_y_train = transform_train
    xgb_r = xg.XGBRegressor(
        objective="reg:squarederror", eval_metric=mean_absolute_error, n_estimators=20
    )
    xgb_r.fit(transformed_X_train, transformed_y_train)
    transformed_X_test, transformed_y_test = transform_test
    score = xgb_r.score(transformed_X_test, transformed_y_test)
    return xgb_r, score


## models_end


@asset
def reg_model(transform_train, transform_test):
    vectorizer, transformed_X_train, transformed_y_train = transform_train
    reg = linear_model.LinearRegression()
    reg.fit(transformed_X_train, transformed_y_train)
    transformed_X_test, transformed_y_test = transform_test
    score = reg.score(transformed_X_test, transformed_y_test)
    return reg, score
