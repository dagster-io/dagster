from hashlib import sha256

from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.logical_version import DEFAULT_LOGICAL_VERSION
from dagster._core.test_utils import instance_for_test


def _make_hash(*inputs):
    hash_sig = sha256()
    hash_sig.update(bytearray("".join(inputs), "utf8"))
    return hash_sig.hexdigest()
        
def test_get_most_recent_logical_version():

    with instance_for_test() as instance:
        


def test_get_logical_version_from_inputs():

    @asset
    def alpha():
        pass

    @asset
    def beta():
        pass

    @asset
    def delta(alpha, beta):
        pass

    op_version = "foo"

    with instance_for_test() as instance:

        value = _make_hash(op_version, DEFAULT_LOGICAL_VERSION.value, DEFAULT_LOGICAL_VERSION.value)

        ver = instance.get_logical_version_from_inputs(
            {alpha.key, beta.key},
            op_version,
            {
                alpha.key: False,
                beta.key: False,
            },
        )
        assert ver.value == value
