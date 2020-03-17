import os

from dagster import check

from .config_type import ConfigIntInstance, ConfigStringInstance, ScalarUnion
from .field_utils import Selector


class StringSourceType(ScalarUnion):
    def __init__(self):
        super(StringSourceType, self).__init__(
            scalar_type=ConfigStringInstance,
            non_scalar_type=Selector({'env': str}),
            _key='StringSourceType',
        )

    def post_process(self, value):
        if not isinstance(value, dict):
            return value

        key, cfg = list(value.items())[0]
        if key == 'env':
            value = os.getenv(cfg)
            check.invariant(
                value is not None, 'Environment variable "{var}" is not set.'.format(var=cfg)
            )
            return value
        else:
            check.failed('Invalid source selector key')


class IntSourceType(ScalarUnion):
    def __init__(self):
        super(IntSourceType, self).__init__(
            scalar_type=ConfigIntInstance,
            non_scalar_type=Selector({'env': str}),
            _key='IntSourceType',
        )

    def post_process(self, value):
        if not isinstance(value, dict):
            return value

        key, cfg = list(value.items())[0]
        if key == 'env':
            value = os.getenv(cfg)
            check.invariant(
                value is not None, 'Environment variable "{var}" is not set.'.format(var=cfg)
            )
            return int(value)
        else:
            check.failed('Invalid source selector key')


StringSource = StringSourceType()
IntSource = IntSourceType()
