from dagster import EventMetadataEntry, ExpectationResult, check


def create_expectation_result(label, ge_evr):
    check.dict_param(ge_evr, 'ge_evr', key_type=str)
    check.param_invariant('success' in ge_evr, 'ge_evr')
    return ExpectationResult(
        success=ge_evr['success'],
        label=label,
        metadata_entries=[EventMetadataEntry.json(ge_evr, label='evr')],
    )


def expectation_results_from_validation(validation):
    for validation_result in validation['results']:
        check.invariant('expectation_config' in validation_result, 'must have expectation_config')
        yield create_expectation_result(
            label=validation_result['expectation_config']['expectation_type'],
            # validation_result appears to be a strict superset of the core evr
            # ge type. A sort of informal, untyped, mixin.
            ge_evr=validation_result,
        )


def expectation_result_list_from_validation(validation):
    return list(expectation_results_from_validation(validation))
