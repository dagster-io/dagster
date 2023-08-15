# ruff: isort: skip_file

## eager_materilization_start

from dagster import AutoMaterializePolicy, asset


@asset
def my_data():
    ...


@asset(
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def my_ml_model(my_data):
    ...


## eager_materilization_end

## lazy_materlization_start

from dagster import AutoMaterializePolicy, asset, FreshnessPolicy


@asset
def my_other_data():
    ...


@asset(
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=7 * 24 * 60),
)
def my_other_ml_model(my_other_data):
    ...


## lazy_materlization_end


## without_policy_start
from dagster import AutoMaterializePolicy, FreshnessPolicy, asset


@asset
def some_data():
    ...


@asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
def some_ml_model(some_data):
    ...


@asset(
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=7 * 24 * 60),
)
def predictions(some_ml_model):
    ...


## without_policy_end

## basic_schedule_start

from dagster import AssetSelection, define_asset_job, ScheduleDefinition

ml_asset_job = define_asset_job("ml_asset_job", AssetSelection.groups("ml_asset_group"))

basic_schedule = ScheduleDefinition(job=ml_asset_job, cron_schedule="0 9 * * *")

## basic_schedule_end

## conditional_monitoring_start

from sklearn import linear_model
from dagster import asset, Output, AssetKey
import numpy as np
from sklearn.model_selection import train_test_split


@asset(output_required=False)
def conditional_machine_learning_model(context):
    X, y = np.random.randint(5000, size=(5000, 2)), range(5000)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.33, random_state=42
    )
    reg = linear_model.LinearRegression()
    reg.fit(X_train, y_train)

    # Get the model accuracy from metadata of the previous materilization of this machine learning model
    instance = context.instance
    materialization = instance.get_latest_materialization_event(
        AssetKey(["conditional_machine_learning_model"])
    )
    if materialization is None:
        yield Output(reg, metadata={"model_accuracy": reg.score(X_test, y_test)})

    else:
        previous_model_accuracy = materialization.asset_materialization.metadata[
            "model_accuracy"
        ]
        new_model_accuracy = reg.score(X_test, y_test)
        if new_model_accuracy > previous_model_accuracy:
            yield Output(reg, metadata={"model_accuracy": new_model_accuracy})


## conditional_monitoring_end


@asset
def ml_model():
    pass


slack_token = "782823"

## fail_slack_start

import os
from dagster import define_asset_job
from dagster_slack import make_slack_on_run_failure_sensor

ml_job = define_asset_job("ml_training_job", selection=[ml_model])

slack_on_run_failure = make_slack_on_run_failure_sensor(
    channel="#ml_monitor_channel",
    slack_token=slack_token,
    monitored_jobs=([ml_job]),
)
## fail_slack_end

## ui_plot_start
from dagster import MetadataValue
import seaborn
import matplotlib.pyplot as plt
import base64
from io import BytesIO


def make_plot(eval_metric):
    plt.clf()
    training_plot = seaborn.lineplot(eval_metric)
    fig = training_plot.get_figure()
    buffer = BytesIO()
    fig.savefig(buffer)
    image_data = base64.b64encode(buffer.getvalue())
    return MetadataValue.md(f"![img](data:image/png;base64,{image_data.decode()})")


## ui_plot_end

from docs_snippets.guides.dagster.ml_pipelines.ml_pipeline import (
    transformed_test_data,
    transformed_train_data,
)

## metadata_use_start

from dagster import asset
import xgboost as xgb
from sklearn.metrics import mean_absolute_error


@asset
def xgboost_comments_model(transformed_training_data, transformed_test_data):
    transformed_X_train, transformed_y_train = transformed_training_data
    transformed_X_test, transformed_y_test = transformed_test_data
    # Train XGBoost model, which is a highly efficient and flexible model
    xgb_r = xgb.XGBRegressor(
        objective="reg:squarederror", eval_metric=mean_absolute_error, n_estimators=20
    )
    xgb_r.fit(
        transformed_X_train,
        transformed_y_train,
        eval_set=[(transformed_X_test, transformed_y_test)],
    )

    ## plot the mean absolute error values as the training progressed
    metadata = {}
    for eval_metric in xgb_r.evals_result()["validation_0"].keys():
        metadata[f"{eval_metric} plot"] = make_plot(
            xgb_r.evals_result_["validation_0"][eval_metric]
        )
    # keep track of the score
    metadata["score (mean_absolute_error)"] = xgb_r.evals_result_["validation_0"][
        "mean_absolute_error"
    ][-1]

    return Output(xgb_r, metadata=metadata)


## metadata_use_end
