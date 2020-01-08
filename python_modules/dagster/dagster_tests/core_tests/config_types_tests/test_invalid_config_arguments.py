import pytest

from dagster import DagsterInvalidConfigDefinitionError, solid


def test_bad_solid_config_argument():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config='dkjfkd')
        def _bad_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: 'dkjfkd'. 'dkjfkd' cannot be resolved."
    )


def test_bad_solid_config_argument_nested():
    with pytest.raises(DagsterInvalidConfigDefinitionError) as exc_info:

        @solid(config={'field': 'kdjkfjd'})
        def _bad_config(_):
            pass

    assert str(exc_info.value).startswith(
        "Error defining config. Original value passed: {'field': 'kdjkfjd'}. "
        "Error at stack path :field. 'kdjkfjd' cannot be resolved."
    )
