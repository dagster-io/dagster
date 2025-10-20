import pytest
from kubernetes.client import models
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def rolebinding_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/rolebinding.yaml",
        model=models.V1RoleBinding,
    )


def test_rolebinding_renders_correctly(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        rbacEnabled=True,
        serviceAccount={"name": "custom-service-account"},
    )

    [rolebinding] = template.render(helm_values)

    assert rolebinding.metadata.name == "release-name-dagster-rolebinding"
    assert rolebinding.metadata.labels["app"] == "dagster"

    assert len(rolebinding.subjects) == 1
    subject = rolebinding.subjects[0]
    assert subject.kind == "ServiceAccount"
    assert subject.name == "custom-service-account"

    assert rolebinding.role_ref.api_group == "rbac.authorization.k8s.io"
    assert rolebinding.role_ref.kind == "Role"
    assert rolebinding.role_ref.name == "release-name-dagster-role"
