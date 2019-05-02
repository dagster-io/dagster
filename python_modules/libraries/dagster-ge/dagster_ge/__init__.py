import copy
import json

import great_expectations as ge

from dagster import check
from dagster.core.definitions import ExpectationDefinition, ExpectationResult


# e.g.
# expectations=[
#     dagster_ge.json_config_expectation('num_expectations', 'num_expectations.json')
# ]
def json_config_expectation(name, file_path):
    def _file_passes(_info, df):
        with open(file_path) as ff:
            expt_config = json.load(ff)
            # This is necessary because ge ends up coercing a type change
            # on the same dataframe instance, changing the type. But a
            # ge can't be copied, because it causes an error.
            # The error is
            #  AttributeError: 'PandasDataset' object has no attribute
            #  'discard_subset_failing_expectations'
            # See https://github.com/great-expectations/great_expectations/issues/342
            df_copy = copy.deepcopy(df)
            ge_df = ge.from_pandas(df_copy, expectations_config=expt_config)
            validate_result = ge_df.validate()
            check.invariant('success' in validate_result)
            check.invariant('results' in validate_result)
            return ExpectationResult(
                success=validate_result['success'], result_metadata=validate_result
            )

    return ExpectationDefinition(name, expectation_fn=_file_passes)


# e.g.
# expectations=[
#   dagster_ge.ge_expectation(name, lambda ge_df: ge_df.expect_column_to_exist(col_name)),
# ]
def ge_expectation(name, ge_callback):
    def _do_expectation(_info, df):
        ge_df = ge.from_pandas(df)
        ge_result = ge_callback(ge_df)
        check.invariant('success' in ge_result)
        return ExpectationResult(success=ge_result['success'], result_metadata=ge_result)

    return ExpectationDefinition(name, expectation_fn=_do_expectation)
