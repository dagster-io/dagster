"""The `pex_bundle` marker lets the server identify PEX-origin images."""

from dagster_cloud_cli.commands.ci.state import DockerBuildOutput
from dagster_cloud_cli.config_utils import get_location_document


def test_docker_build_output_defaults_to_not_a_bundle():
    assert DockerBuildOutput(image="img:tag").pex_bundle is False
    assert DockerBuildOutput(image="img:tag", pex_bundle=True).pex_bundle is True


def test_get_location_document_stamps_pex_bundle_when_set():
    doc = get_location_document("loc", {"image": "img:tag", "pex_bundle": True})
    assert doc["pex_bundle"] is True


def test_get_location_document_omits_pex_bundle_by_default():
    # remove_none_recursively drops the field, so native docker deploys carry no marker.
    doc = get_location_document("loc", {"image": "img:tag"})
    assert "pex_bundle" not in doc
