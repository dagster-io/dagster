import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/secret-postgres.yaml",
        model=models.V1Secret,
    )


def test_postgresql_secret_does_not_render(template: HelmTemplate):
    with pytest.raises(subprocess.CalledProcessError):
        helm_values_generate_postgresql_secret_disabled = DagsterHelmValues.construct(
            generatePostgresqlPasswordSecret=False
        )

        template.render(helm_values_generate_postgresql_secret_disabled)


def test_postgresql_secret_renders(template: HelmTemplate):
    helm_values_generate_postgresql_secret_enabled = DagsterHelmValues.construct(
        generatePostgresqlPasswordSecret=True
    )

    secrets = template.render(helm_values_generate_postgresql_secret_enabled)

    assert len(secrets) == 1
