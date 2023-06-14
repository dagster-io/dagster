# isort: skip_file
from dask.distributed import Client
from dagster import ConfigurableResource


class DaskResource(ConfigurableResource):
    def make_dask_cluster(self) -> Client:
        client = Client()
        return client


## first_snippet_start

from dask_ml.datasets import make_classification
from dagster import asset, MetadataValue


@asset
def my_classification_data(context, MyDaskResource: DaskResource):
    client = MyDaskResource.make_dask_cluster()
    X, y = make_classification(chunks=200, n_samples=10000)
    return X, y


## first_snippet_end

## second_snippet_start
from dagster import multi_asset, AssetOut
from dask_ml import model_selection


@multi_asset(outs={"training_data": AssetOut(), "test_data": AssetOut()})
def train_test_data(context, MyDaskResource: DaskResource, my_classification_data):
    client = MyDaskResource.make_dask_cluster()
    X, y = my_classification_data
    X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y)
    return (X_train, y_train), (X_test, y_test)


## second_snippet_end

## third_snippet_start
from sklearn.linear_model import SGDClassifier
from dask_ml.model_selection import HyperbandSearchCV
import numpy as np


@asset
def my_model(context, MyDaskResource: DaskResource, training_data):
    client = MyDaskResource.make_dask_cluster()
    X_train, y_train = training_data
    est = SGDClassifier(tol=1e-3)
    param_dist = {
        "alpha": np.logspace(-4, 0, num=1000),
        "loss": ["hinge", "log", "modified_huber", "squared_hinge"],
        "average": [True, False],
    }
    search = HyperbandSearchCV(est, param_dist)
    search.fit(X_train, y_train, classes=np.unique(y_train))
    metadata = search.best_params_
    context.add_output_metadata(metadata)
    model = search.best_estimator_
    return model


## third_snippet_end


## fourth_snippet_start
@asset
def my_score(context, MyDaskResource: DaskResource, test_data, my_model):
    client = MyDaskResource.make_dask_cluster()
    X_test, y_test = test_data
    my_score = my_model.score(X_test, y_test)
    context.add_output_metadata({"score": my_score})
    return my_score


## fourth_snippet_end

## fifth_snippet_start
from dagster import Definitions

defs = Definitions(
    assets=[my_classification_data, train_test_data, my_model, my_score],
    resources={"MyDaskResource": DaskResource()},
)
## fifth_snippet_end
