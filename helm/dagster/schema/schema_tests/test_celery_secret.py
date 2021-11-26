import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.run_launcher import RunLauncher, RunLauncherType
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/secret-celery-config.yaml",
        model=models.V1Secret,
    )


def test_celery_secret_does_not_render(template: HelmTemplate):
    with pytest.raises(subprocess.CalledProcessError):
        helm_values_generate_celery_secret_disabled = DagsterHelmValues.construct(
            generateCeleryConfigSecret=False
        )

        template.render(helm_values_generate_celery_secret_disabled)


def test_celery_secret_does_not_render_without_celery_run_launcher(template: HelmTemplate):
    with pytest.raises(subprocess.CalledProcessError):
        helm_values_generate_celery_secret_enabled_no_run_launcher = DagsterHelmValues.construct(
            generateCeleryConfigSecret=True
        )
        template.render(helm_values_generate_celery_secret_enabled_no_run_launcher)


def test_celery_secret_renders(template: HelmTemplate):
    helm_values_generate_celery_secret_enabled = DagsterHelmValues.construct(
        generateCeleryConfigSecret=True,
        runLauncher=RunLauncher.construct(type=RunLauncherType.CELERY),
    )

    secrets = template.render(helm_values_generate_celery_secret_enabled)

    assert len(secrets) == 1
