from dagster import AssetKey, AssetSpec
from dagster_airlift.k8s import k8s_pod_defs


def test_asset_construction() -> None:
    """Test that underlying asset has the expected structure."""
    defs = k8s_pod_defs(
        specs=[AssetSpec("asset1"), AssetSpec("asset2")],
        pod_spec={},
        pod_metadata={},
        load_incluster_config=False,
        kube_context="minikube",
        kubeconfig_file="",
    )
    assets_defs = defs.get_asset_graph().assets_defs
    assert len(assets_defs) == 1
    assert len(list(assets_defs[0].specs)) == 2
    assert any(spec.key == AssetKey("asset1") for spec in assets_defs[0].specs)
    assert any(spec.key == AssetKey("asset2") for spec in assets_defs[0].specs)
    assert assets_defs[0].is_executable
