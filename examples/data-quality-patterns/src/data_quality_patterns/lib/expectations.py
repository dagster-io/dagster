"""Great Expectations integration utilities."""

import pandas as pd
from great_expectations.dataset import PandasDataset


def create_ge_dataset(df: pd.DataFrame) -> PandasDataset:
    """Create a Great Expectations dataset from a pandas DataFrame.

    Args:
        df: pandas DataFrame to convert

    Returns:
        Great Expectations PandasDataset
    """
    return PandasDataset(df)
