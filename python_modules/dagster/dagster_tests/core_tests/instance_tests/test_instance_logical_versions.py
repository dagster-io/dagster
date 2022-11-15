from hashlib import sha256

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.logical_version import DEFAULT_LOGICAL_VERSION
from dagster._core.definitions.materialize import materialize
from dagster._core.test_utils import instance_for_test


def _make_hash(*inputs):
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(inputs), "utf8"))
    return hash_sig.hexdigest()


def test_get_most_recent_logical_version():
    @asset
    def alpha():
        pass

    @asset
    def beta():
        pass

    @asset
    def delta(alpha, beta):  # pylint: disable=unused-argument
        pass

    with instance_for_test() as instance:
        assert instance.get_current_logical_version(delta.key, False) == DEFAULT_LOGICAL_VERSION
        materialize([delta, beta, alpha], instance=instance)
        assert instance.get_current_logical_version(delta.key, False) != DEFAULT_LOGICAL_VERSION
