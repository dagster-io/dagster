
## data_ingestion_start
import requests
from dagster import asset, FreshnessPolicy
import pandas as pd

@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=10))
def hackernews_stories():
    """Get the max ID number from hacker news"""

    latest_item = requests.get(
        f"https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()

    """Get items based on story ids from the HackerNews items endpoint"""
    results = []
    scope = range(latest_item-1000, latest_item)
    for item_id in scope:
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
        ).json()
        results.append(item)

    df = pd.DataFrame(results)
    if len(df) > 0:
        df = df[df.type == "story"]
        df = df[~df.title.isna()]

    return df


## data_ingestion_end

## test_train_split_start

from sklearn.model_selection import train_test_split
from dagster import multi_asset, AssetOut

@multi_asset(outs={'training_data': AssetOut(), 'test_data': AssetOut()})
def training_test_data(hackernews_stories):
    hackernews_stories = hackernews_stories
    X = hackernews_stories.title
    y = hackernews_stories.descendants
    """Split the dataset to reserve 20% of records as the test set"""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train,  y_train), (X_test, y_test)


## test_train_split_end


## vectorizer_start
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

@multi_asset(outs={'Tfidf_Vectorizer': AssetOut(), 'transformed_training_data': AssetOut()})
def transformed_train(training_data):
    X_train,  y_train = training_data
    """Initiate and fit the tokenizer on the training data and transform the training dataset"""
    vectorizer = TfidfVectorizer()
    transformed_X_train = vectorizer.fit_transform(X_train)
    transformed_X_train = transformed_X_train.toarray()
    y_train = y_train.fillna(0)
    transformed_y_train = np.array(y_train)

    return vectorizer, (transformed_X_train, transformed_y_train)


@asset
def transformed_test_data(test_data, Tfidf_Vectorizer):
    X_test, y_test = test_data
        """Use the fitted tokenizer to transform the test dataset"""
    transformed_X_test = Tfidf_Vectorizer.transform(X_test)
    transformed_y_test = np.array(y_test)
    y_test = y_test.fillna(0)
    transformed_y_test = np.array(y_test)
    return transformed_X_test, transformed_y_test
## vectorizer_end


## models_start

import xgboost as xg
from sklearn.metrics import mean_absolute_error

@asset
def xgboost(transformed_training_data):
    transformed_X_train, transformed_y_train = transformed_training_data
    """Train XGBoost model, which is a highly efficent and flexible model"""
    xgb_r = xg.XGBRegressor(objective ='reg:squarederror', eval_metric=mean_absolute_error,
                  n_estimators = 20)
    xgb_r.fit(transformed_X_train, transformed_y_train)
    return xgb_r

@asset 
def score_xgboost( transformed_test_data, xgboost):
    transformed_X_test, transformed_y_test = transformed_test_data
    """Use the test set data to get a score of the XGBoost model"""
    score = xgboost.score(transformed_X_test, transformed_y_test)
    return score 
## models_end


## inference_start
@asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=60))
def model_inference(xgboost, Tfidf_Vectorizer):
    """Get the max ID number from hacker news"""

    latest_item = requests.get(
        f"https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()

    """Get items based on story ids from the HackerNews items endpoint"""
    results = []
    scope = range(latest_item-100, latest_item)
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
    inference_x = Tfidf_Vectorizer.transform(inference_x)
    return xgboost.predict(inference_x)

## inference_end

    

