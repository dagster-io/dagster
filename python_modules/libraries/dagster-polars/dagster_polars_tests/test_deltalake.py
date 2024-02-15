# seems like the problems with reading/writing delta tables are only happening when
# doing this very fast, i.e. in a test.
# commenting this for now

import shutil

import polars as pl
import polars.testing as pl_testing
from _pytest.tmpdir import TempPathFactory
from hypothesis import given, settings
from polars.testing.parametric import dataframes


@given(
    df=dataframes(
        excluded_dtypes=[
            pl.Categorical,  # Unsupported type in delta protocol
            pl.Duration,  # Unsupported type in delta protocol
            pl.Time,  # Unsupported type in delta protocol
            pl.UInt8,  # These get casted to int in deltalake whenever it fits
            pl.UInt16,  # These get casted to int in deltalake whenever it fits
            pl.UInt32,  # These get casted to int in deltalake whenever it fits
            pl.UInt64,  # These get casted to int in deltalake whenever it fits
            pl.Datetime("ns", None),  # These get casted to datetime('ms')
        ],
        min_size=5,
        allow_infinities=False,
    )
)
@settings(max_examples=20, deadline=None)
def test_polars_delta_io(df: pl.DataFrame, tmp_path_factory: TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("data")
    df.write_delta(str(tmp_path), delta_write_options={"engine": "rust"})
    pl_testing.assert_frame_equal(df.with_columns(), pl.read_delta(str(tmp_path)))
    shutil.rmtree(str(tmp_path))  # cleanup manually because of hypothesis
