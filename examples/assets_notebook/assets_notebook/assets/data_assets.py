from dagster import asset

import pandas as pd
import numpy as np
from sklearn import datasets


@asset
def iris_dataset():
    sk_iris = datasets.load_iris()
    return pd.DataFrame(
        data=np.c_[sk_iris["data"], sk_iris["target"]],
        columns=sk_iris["feature_names"] + ["target"],
    )