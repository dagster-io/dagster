import requests
from dagster import asset, Output, MetadataValue, SourceAsset
import pandas as pd 
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error
import mlflow
import mlflow.xgboost
import mlflow.pyfunc
import os
import numpy as np 


import pickle 

## Transformated data from the basic machine learning example is used for this example, to generate the datasets, please refer to that example 
@asset
def transformed_training_data():
    return pickle.load(open('./data_sources/transformed_training_data', 'rb'))

@asset
def transformed_test_data():
   return pickle.load(open('./data_sources/transformed_test_data', 'rb'))
    
@asset
def tfidf_vectorizer():
    return pickle.load(open('./data_sources/tfidf_vectorizer', 'rb'))
    
port = '5000'


@asset(compute_kind='xgboost')
def xgboost_comments_model_mlflow(transformed_training_data, transformed_test_data):
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

    # cmd = f'mlflow ui --port {PORT}'
    # os.system(cmd)

    # url = f"http://127.0.0.1:{PORT}"
    # link = f"{url}/#/experiments/{experiment_id}/runs/{run_id}"
    # my_metadata["mlflow link"] = MetadataValue.url(link)
    return Output(xgb_regressor, metadata= my_metadata)


@asset(compute_kind='mlflow')
def model_registry_mlflow(xgboost_comments_model_mlflow):

    registry = mlflow.xgboost.log_model(
    xgb_model=xgboost_comments_model_mlflow,
    artifact_path="xgboost_comments_model",
    registered_model_name="xgboost_comments_model")

    latest_version = dict(mlflow.MlflowClient().search_model_versions("name='xgboost_comments_model'")[0])['version']
    
    # model_name = 'xgboost'

    model = mlflow.pyfunc.load_model(model_uri=f"models:/{'xgboost_comments_model'}/{latest_version}")
    url = f"http://127.0.0.1:{port}"
    model_link =  MetadataValue.url(f"{url}//#/models/xgboost_comments_model/versions/{latest_version}")
    return Output(model, metadata= {"version" :latest_version, 'model registry link': model_link})


@asset(compute_kind='mlflow', non_argument_deps={"model_registry"})
def latest_story_comment_predictions_mlflow(tfidf_vectorizer):
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

    latest_version = dict(mlflow.MlflowClient().search_model_versions("name='xgboost_comments_model'")[0])['version']
    latest_model = mlflow.pyfunc.load_model(model_uri=f"models:/{'xgboost_comments_model'}/{latest_version}")

    return latest_model.predict(inference_x)





