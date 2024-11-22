import os

import dagster._check as check
from dagster._config.config_type import ScalarUnion
from dagster._config.errors import PostProcessingError
from dagster._config.field_utils import Selector

VALID_STRING_SOURCE_TYPES = (str, dict)


def _ensure_env_variable(var):
    check.str_param(var, "var")
    value = os.getenv(var)
    if value is None:
        raise PostProcessingError(
            f'You have attempted to fetch the environment variable "{var}" '
            "which is not set. In order for this execution to succeed it "
            "must be set in this environment."
        )
    return value


class StringSourceType(ScalarUnion):
    def __init__(self):
        super().__init__(
            scalar_type=str,
            non_scalar_schema=Selector({"env": str}),
            _key="StringSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, VALID_STRING_SOURCE_TYPES), "value")

        if not isinstance(value, dict):
            return value

        key, cfg = next(iter(value.items()))
        check.invariant(key == "env", "Only valid key is env")
        return str(_ensure_env_variable(cfg))


class IntSourceType(ScalarUnion):
    def __init__(self):
        super().__init__(
            scalar_type=int,
            non_scalar_schema=Selector({"env": str}),
            _key="IntSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, (dict, int)), "value", "Should be pre-validated")

        if not isinstance(value, dict):
            return value

        check.invariant(len(value) == 1, "Selector should have one entry")

        key, cfg = next(iter(value.items()))
        check.invariant(key == "env", "Only valid key is env")
        value = _ensure_env_variable(cfg)
        try:
            return int(value)
        except ValueError as e:
            raise PostProcessingError(
                f'Value "{value}" stored in env variable "{cfg}" cannot be coerced into an int.'
            ) from e


class BoolSourceType(ScalarUnion):
    def __init__(self):
        super().__init__(
            scalar_type=bool,
            non_scalar_schema=Selector({"env": str}),
            _key="BoolSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, (dict, bool)), "value", "Should be pre-validated")

        if not isinstance(value, dict):
            return value

        check.invariant(len(value) == 1, "Selector should have one entry")

        key, cfg = next(iter(value.items()))
        check.invariant(key == "env", "Only valid key is env")
        value = _ensure_env_variable(cfg)
        try:
            return bool(value)
        except ValueError as e:
            raise PostProcessingError(
                f'Value "{value}" stored in env variable "{cfg}" cannot be coerced into an bool.'
            ) from e


StringSource: StringSourceType = StringSourceType()
IntSource: IntSourceType = IntSourceType()
BoolSource: BoolSourceType = BoolSourceType()
