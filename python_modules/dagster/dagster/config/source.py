import os

from dagster import check

from .config_type import ScalarUnion
from .errors import PostProcessingError
from .field_utils import Selector

VALID_STRING_SOURCE_TYPES = (str, dict)


def _ensure_env_variable(var):
    check.str_param(var, "var")
    value = os.getenv(var)
    if value is None:
        raise PostProcessingError(
            (
                'You have attempted to fetch the environment variable "{var}" '
                "which is not set. In order for this execution to succeed it "
                "must be set in this environment."
            ).format(var=var)
        )
    return value


class StringSourceType(ScalarUnion):
    def __init__(self):
        super(StringSourceType, self).__init__(
            scalar_type=str,
            non_scalar_schema=Selector({"env": str}),
            _key="StringSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, VALID_STRING_SOURCE_TYPES), "value")

        if not isinstance(value, dict):
            return value

        key, cfg = list(value.items())[0]
        check.invariant(key == "env", "Only valid key is env")
        return str(_ensure_env_variable(cfg))


class IntSourceType(ScalarUnion):
    def __init__(self):
        super(IntSourceType, self).__init__(
            scalar_type=int,
            non_scalar_schema=Selector({"env": str}),
            _key="IntSourceType",
        )

    def post_process(self, value):
        check.param_invariant(isinstance(value, (dict, int)), "value", "Should be pre-validated")

        if not isinstance(value, dict):
            return value

        check.invariant(len(value) == 1, "Selector should have one entry")

        key, cfg = list(value.items())[0]
        check.invariant(key == "env", "Only valid key is env")
        value = _ensure_env_variable(cfg)
        try:
            return int(value)
        except ValueError:
            raise PostProcessingError(
                (
                    'Value "{value}" stored in env variable "{var}" cannot be '
                    "coerced into an int."
                ).format(value=value, var=cfg)
            )


StringSource = StringSourceType()
IntSource = IntSourceType()
