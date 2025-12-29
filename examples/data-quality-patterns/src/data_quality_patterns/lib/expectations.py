"""Great Expectations integration utilities."""

from typing import Any, Optional

import pandas as pd

try:
    from great_expectations.dataset import PandasDataset

    GE_AVAILABLE = True
except ImportError:
    GE_AVAILABLE = False
    PandasDataset = None


def create_ge_dataset(df: pd.DataFrame) -> Optional[Any]:
    """Create a Great Expectations dataset from a pandas DataFrame.

    Args:
        df: pandas DataFrame to convert

    Returns:
        Great Expectations PandasDataset, or None if GE is not available
    """
    if not GE_AVAILABLE or PandasDataset is None:
        return None

    return PandasDataset(df)
