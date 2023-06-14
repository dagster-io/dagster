import requests
from dagster import asset, multi_asset, AssetOut, Output, MetadataValue
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import xgboost as xg
from sklearn.metrics import mean_absolute_error

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


@multi_asset(outs={"training_data": AssetOut(), "test_data": AssetOut()})
def training_test_data(hackernews_stories):
    hackernews_stories = hackernews_stories
    X = hackernews_stories.title
    y = hackernews_stories.descendants

    # Split the dataset to reserve 20% of records as the test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train, y_train), (X_test, y_test)

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

import seaborn
import matplotlib.pyplot as plt
import base64
from io import BytesIO


@asset
def xgboost_comments_model(transformed_training_data, transformed_test_data):
    transformed_X_train, transformed_y_train = transformed_training_data
    transformed_X_test, transformed_y_test = transformed_test_data

    # Train XGBoost model, which is a highly efficient and flexible model
    xgb_r = xg.XGBRegressor(
        objective="reg:squarederror", eval_metric=mean_absolute_error, n_estimators=20
    )
    xgb_r.fit(transformed_X_train, transformed_y_train, eval_set=[(transformed_X_test, transformed_y_test)])


    ## plot the mean absolute error values as the training progressed
    metadata = {}
    for eval_metric in xgb_r.evals_result()['validation_0'].keys():
        metadata[f'{eval_metric} plot'] = make_plot(xgb_r.evals_result_['validation_0'][eval_metric])
    # keep track of the score 

    metadata['score (mean_absolute_error)'] = xgb_r.evals_result_['validation_0']['mean_absolute_error'][-1]

    return Output(xgb_r, metadata=metadata)

def make_plot(eval_metric):
    plt.clf()
    training_plot = seaborn.lineplot(eval_metric)
    fig = training_plot.get_figure()
    buffer = BytesIO()
    fig.savefig(buffer)
    image_data = base64.b64encode(buffer.getvalue())
    return MetadataValue.md(f"![img](data:image/png;base64,{image_data.decode()})")


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


