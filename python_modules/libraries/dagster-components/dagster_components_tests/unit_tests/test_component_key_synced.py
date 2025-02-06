import inspect


def test_component_key_synced() -> None:
    """Because these modules cannot share a dependency outside of tests, we rely on a janky unit test
    to make sure their definitions remain in sync.
    """
    import dagster_components.core.component_key as dagster_components_component_key
    import dagster_dg.component_key as dagster_dg_component_key

    assert inspect.getsource(dagster_components_component_key) == inspect.getsource(
        dagster_dg_component_key
    )
