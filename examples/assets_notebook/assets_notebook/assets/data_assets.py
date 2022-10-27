import numpy as np
import pandas as pd
from sklearn import datasets

from dagster import asset


@asset
def iris_dataset():
    sk_iris = datasets.load_iris()
    return pd.DataFrame(
        data=np.c_[sk_iris["data"], sk_iris["target"]],
        columns=sk_iris["feature_names"] + ["target"],
    )