import subprocess

import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.migrate import Migrate
from schema.charts.dagster.subschema.webserver import (
    Webserver,
)
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/job-instance-migrate.yaml",
        model=models.V1Job,
    )


def test_job_instance_migrate_does_not_render(template: HelmTemplate, capfd):
    with pytest.raises(subprocess.CalledProcessError):
        helm_values_migrate_disabled = DagsterHelmValues.construct(migrate=Migrate(enabled=False))

        template.render(helm_values_migrate_disabled)

    _, err = capfd.readouterr()
    assert "Error: could not find template" in err


def test_job_instance_migrate_renders(template: HelmTemplate):
    helm_values_migrate_enabled = DagsterHelmValues.construct(migrate=Migrate(enabled=True))

    jobs = template.render(helm_values_migrate_enabled)

    assert len(jobs) == 1


@pytest.mark.parametrize("chart_version", ["0.12.0", "0.12.1"])
def test_job_instance_migrate_image(template: HelmTemplate, chart_version: str):
    helm_values_migrate_enabled = DagsterHelmValues.construct(migrate=Migrate(enabled=True))

    [job] = template.render(helm_values_migrate_enabled, chart_version=chart_version)
    image = job.spec.template.spec.containers[0].image
    _, tag = image.split(":")

    assert tag == chart_version


def test_job_instance_migrate_keeps_annotations(template: HelmTemplate):
    annotations = {"annotation_1": "an_annotation_1", "annotation_2": "an_annotation_2"}

    helm_values_migrate_enabled = DagsterHelmValues.construct(
        migrate=Migrate(enabled=True),
        dagsterWebserver=Webserver.construct(
            annotations=kubernetes.Annotations.parse_obj(annotations),
        ),
    )

    jobs = template.render(helm_values_migrate_enabled)

    assert len(jobs) == 1

    job = jobs[0]

    assert job.metadata.annotations == annotations
    assert job.spec.template.metadata.annotations == annotations
