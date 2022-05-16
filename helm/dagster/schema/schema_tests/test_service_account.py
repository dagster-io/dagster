import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.global_ import Global
from schema.charts.dagster.subschema.service_account import ServiceAccount
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def umbrella_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/serviceaccount.yaml",
        model=models.V1ServiceAccount,
    )


@pytest.fixture(name="subchart_template")
def subchart_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="charts/dagster-user-deployments/templates/serviceaccount.yaml",
        model=models.V1ServiceAccount,
    )


@pytest.fixture(name="standalone_subchart_template")
def standalone_subchart_helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster/charts/dagster-user-deployments",
        subchart_paths=[],
        output="templates/serviceaccount.yaml",
        model=models.V1ServiceAccount,
    )


def test_service_account_name(template: HelmTemplate):
    service_account_name = "service-account-name"
    service_account_values = DagsterHelmValues.construct(
        serviceAccount=ServiceAccount.construct(name=service_account_name, create=True)
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name


def test_service_account_global_name(template: HelmTemplate):
    global_service_account_name = "global-service-account-name"
    service_account_values = DagsterHelmValues.construct(
        global_=Global.construct(serviceAccountName=global_service_account_name),
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == global_service_account_name


def test_subchart_service_account_global_name(subchart_template: HelmTemplate, capfd):
    global_service_account_name = "global-service-account-name"
    service_account_values = DagsterHelmValues.construct(
        global_=Global.construct(serviceAccountName=global_service_account_name),
    )

    with pytest.raises(subprocess.CalledProcessError):
        subchart_template.render(service_account_values)

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


def test_standalone_subchart_service_account_name(standalone_subchart_template: HelmTemplate):
    service_account_name = "service-account-name"
    service_account_values = DagsterUserDeploymentsHelmValues.construct(
        serviceAccount=ServiceAccount.construct(name=service_account_name),
    )

    service_account_templates = standalone_subchart_template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name


def test_service_account_does_not_render(template: HelmTemplate, capfd):
    service_account_values = DagsterHelmValues.construct(
        serviceAccount=ServiceAccount.construct(name="service-account-name", create=False),
    )
    with pytest.raises(subprocess.CalledProcessError):
        template.render(service_account_values)

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


def test_service_account_annotations(template: HelmTemplate):
    service_account_name = "service-account-name"
    service_account_annotations = {"hello": "world"}
    service_account_values = DagsterHelmValues.construct(
        serviceAccount=ServiceAccount.construct(
            name=service_account_name, create=True, annotations=service_account_annotations
        )
    )

    service_account_templates = template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name
    assert service_account_template.metadata.annotations == service_account_annotations


def test_standalone_subchart_service_account_annotations(
    standalone_subchart_template: HelmTemplate,
):
    service_account_name = "service-account-name"
    service_account_annotations = {"hello": "world"}
    service_account_values = DagsterUserDeploymentsHelmValues.construct(
        serviceAccount=ServiceAccount.construct(
            name=service_account_name, create=True, annotations=service_account_annotations
        ),
    )

    service_account_templates = standalone_subchart_template.render(service_account_values)

    assert len(service_account_templates) == 1

    service_account_template = service_account_templates[0]

    assert service_account_template.metadata.name == service_account_name
    assert service_account_template.metadata.annotations == service_account_annotations
