import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit
from schema.charts.dagster.subschema.ingress import DagitIngressConfiguration, Ingress, IngressPath
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/ingress.yaml",
        model=models.ExtensionsV1beta1Ingress,
    )


def test_ingress(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            dagit=DagitIngressConfiguration(
                host="foobar.com",
                path="bing",
                precedingPaths=[
                    IngressPath(path="/*", serviceName="ssl-redirect", servicePort="use-annotion")
                ],
                succeedingPaths=[],
            ),
        )
    )

    ingress_template = template.render(helm_values)
    assert len(ingress_template) == 1
    ingress = ingress_template[0]

    assert len(ingress.spec.rules) == 1
    rule = ingress.spec.rules[0]

    assert rule.host == "foobar.com"


def test_ingress_read_only(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            dagit=DagitIngressConfiguration(
                host="foobar.com",
                path="bing",
                precedingPaths=[
                    IngressPath(path="/*", serviceName="ssl-redirect", servicePort="use-annotion")
                ],
                succeedingPaths=[],
            ),
            readOnlyDagit=DagitIngressConfiguration(
                host="dagster.io",
                precedingPaths=[],
                succeedingPaths=[
                    IngressPath(path="/*", serviceName="ssl-redirect", servicePort="use-annotion")
                ],
            ),
        ),
        dagit=Dagit.construct(enableReadOnly=True),
    )

    ingress_template = template.render(helm_values)
    assert len(ingress_template) == 1
    ingress = ingress_template[0]

    assert len(ingress.spec.rules) == 2
    assert [rule.host for rule in ingress.spec.rules] == ["foobar.com", "dagster.io"]
