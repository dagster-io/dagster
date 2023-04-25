import requests
from dagster import asset, Output 
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
import mlflow
import mlflow.xgboost
import mlflow.pyfunc

@asset(compute_kind='HackerNews API')
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


from sklearn.model_selection import train_test_split
from dagster import multi_asset, AssetOut


@multi_asset(outs={"training_data": AssetOut(), "test_data": AssetOut()}, compute_kind='pandas')
def training_test_data(hackernews_stories):
    hackernews_stories = hackernews_stories
    X = hackernews_stories.title
    y = hackernews_stories.descendants
    # Split the dataset to reserve 20% of records as the test set
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return (X_train, y_train), (X_test, y_test)



from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np


@multi_asset(compute_kind='numpy',
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


@asset(compute_kind='numpy')
def transformed_test_data(test_data, tfidf_vectorizer):
    X_test, y_test = test_data
    # Use the fitted tokenizer to transform the test dataset
    transformed_X_test = tfidf_vectorizer.transform(X_test)
    transformed_y_test = np.array(y_test)
    y_test = y_test.fillna(0)
    transformed_y_test = np.array(y_test)
    return transformed_X_test, transformed_y_test




@asset(compute_kind='xgboost')
def xgboost_comments_model(transformed_training_data, transformed_test_data):
    transformed_X_train, transformed_y_train = transformed_training_data
    transformed_X_test, transformed_y_test = transformed_test_data
    # Train XGBoost model, which is a highly efficient and flexible model

    mlflow.xgboost.autolog()
    mlflow.set_experiment("my-experiment")

    xgb_regressor = xgb.XGBRegressor(
        objective="reg:squarederror", eval_metric=mean_absolute_error, n_estimators=20
    )
    xgb_regressor.fit(transformed_X_train, transformed_y_train, eval_set=[(transformed_X_test, transformed_y_test)])

    experiment_id = mlflow.get_experiment_by_name("my-experiment").experiment_id
    run_id = mlflow.last_active_run().info.run_id
    my_run = mlflow.get_run(run_id).to_dictionary()
    my_metadata = my_run['data']['metrics']
    url = "http://127.0.0.1:5000"
    link = f"{url}//#/experiments/{experiment_id}/runs/{run_id}"
    my_metadata["mlflow link"] = link 
    return Output(xgb_regressor, metadata= my_metadata)


@asset(compute_kind='mlflow')
def model_registry(xgboost_comments_model):

    registry = mlflow.xgboost.log_model(
    xgb_model=xgboost_comments_model,
    artifact_path="xgboost_comments_model",
    registered_model_name="xgboost_comments_model")

    latest_version = dict(mlflow.MlflowClient().search_model_versions("name='xgboost_comments_model'")[0])['version']
    
    # model_name = 'xgboost'

    model = mlflow.pyfunc.load_model(model_uri=f"models:/{'xgboost_comments_model'}/{latest_version}")
    url = "http://127.0.0.1:5000"
    model_link =  f"{url}//#/models/xgboost_comments_model/versions/{latest_version}"
    return Output(model, metadata= {"version" :latest_version, 'model registry link': model_link})


@asset(compute_kind='mlflow')
def latest_story_comment_predictions( tfidf_vectorizer):
    # Get the max ID number from hacker news
    latest_item = requests.get(
        "https://hacker-news.firebaseio.com/v0/maxitem.json"
    ).json()
    # Get items based on story ids from the HackerNews items endpoint
    results = []
    scope = range(latest_item - 10, latest_item)
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

    latest_version = dict(mlflow.MlflowClient().search_model_versions("name='xgboost_comments_model'")[0])['version']
    latest_model = mlflow.pyfunc.load_model(model_uri=f"models:/{'xgboost_comments_model'}/{latest_version}")

    return latest_model.predict(inference_x)



