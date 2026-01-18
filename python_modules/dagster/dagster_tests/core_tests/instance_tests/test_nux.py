import dagster as dg


def test_dagster_yaml_nux():
    with dg.instance_for_test() as instance:
        assert instance.nux_enabled
    with dg.instance_for_test(overrides={"nux": {"enabled": True}}) as instance:
        assert instance.nux_enabled
    with dg.instance_for_test(overrides={"nux": {"enabled": False}}) as instance:
        assert not instance.nux_enabled
