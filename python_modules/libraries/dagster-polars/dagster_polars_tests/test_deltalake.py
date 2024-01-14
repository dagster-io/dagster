# seems like the problems with reading/writing delta tables are only happening when
# doing this very fast, i.e. in a test.
# commenting this for now

# import shutil
#
# import polars as pl
# import polars.testing as pl_testing
# from _pytest.tmpdir import TempPathFactory
# from hypothesis import given, settings
# from polars.testing.parametric import dataframes
#
# # TODO: remove pl.Time once it's supported
# # TODO: remove pl.Duration pl.Duration once it's supported
# # https://github.com/pola-rs/polars/issues/9631
# # TODO: remove UInt types once they are fixed:
# #  https://github.com/pola-rs/polars/issues/9627
#
#
# @given(
#     df=dataframes(
#         excluded_dtypes=[
#             pl.Categorical,
#             pl.Duration,
#             pl.Time,
#             pl.UInt8,
#             pl.UInt16,
#             pl.UInt32,
#             pl.UInt64,
#             pl.Datetime("ns", None),
#         ],
#         min_size=5,
#         allow_infinities=False,
#     )
# )
# @settings(max_examples=500, deadline=None)
# def test_polars_delta_io(df: pl.DataFrame, tmp_path_factory: TempPathFactory):
#     tmp_path = tmp_path_factory.mktemp("data")
#     df.write_delta(str(tmp_path))
#     pl_testing.assert_frame_equal(df, pl.read_delta(str(tmp_path)))
#     shutil.rmtree(str(tmp_path))  # cleanup manually because of hypothesis
