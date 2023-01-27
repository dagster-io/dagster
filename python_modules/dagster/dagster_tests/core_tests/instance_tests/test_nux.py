from dagster._core.test_utils import instance_for_test


def test_dagster_yaml_nux():
    with instance_for_test() as instance:
        assert instance.nux_enabled
    with instance_for_test(overrides={"nux": {"enabled": True}}) as instance:
        assert instance.nux_enabled
    with instance_for_test(overrides={"nux": {"enabled": False}}) as instance:
        assert not instance.nux_enabled
