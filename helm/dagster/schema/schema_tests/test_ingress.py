import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.dagit import Dagit
from schema.charts.dagster.subschema.ingress import (
    DagitIngressConfiguration,
    FlowerIngressConfiguration,
    Ingress,
    IngressPath,
    IngressTLSConfiguration,
)
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
            dagit=DagitIngressConfiguration.construct(
                host="foobar.com",
                path="bing",
                precedingPaths=[
                    IngressPath(path="/*", serviceName="ssl-redirect", servicePort="use-annotion")
                ],
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
            dagit=DagitIngressConfiguration.construct(
                host="foobar.com",
                path="bing",
                precedingPaths=[
                    IngressPath(path="/*", serviceName="ssl-redirect", servicePort="use-annotion")
                ],
            ),
            readOnlyDagit=DagitIngressConfiguration.construct(
                host="dagster.io",
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


def test_ingress_tls(template: HelmTemplate):
    dagit_host = "dagit.com"
    dagit_readonly_host = "dagit-readonly.com"
    flower_host = "flower.com"

    dagit_tls_secret_name = "dagit_tls_secret_name"
    dagit_readonly_tls_secret_name = "dagit_readonly_tls_secret_name"
    flower_tls_secret_name = "flower_tls_secret_name"

    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            dagit=DagitIngressConfiguration.construct(
                host=dagit_host,
                tls=IngressTLSConfiguration(enabled=True, secretName=dagit_tls_secret_name),
            ),
            readOnlyDagit=DagitIngressConfiguration.construct(
                host=dagit_readonly_host,
                tls=IngressTLSConfiguration(
                    enabled=True, secretName=dagit_readonly_tls_secret_name
                ),
            ),
            flower=FlowerIngressConfiguration.construct(
                host=flower_host,
                tls=IngressTLSConfiguration(enabled=True, secretName=flower_tls_secret_name),
            ),
        ),
        dagit=Dagit.construct(enableReadOnly=True),
    )

    [ingress] = template.render(helm_values)

    assert len(ingress.spec.tls) == 3

    dagit_tls = ingress.spec.tls[0]
    assert len(dagit_tls.hosts) == 1
    assert dagit_tls.hosts[0] == dagit_host
    assert dagit_tls.secret_name == dagit_tls_secret_name

    dagit_readonly_tls = ingress.spec.tls[1]
    assert len(dagit_readonly_tls.hosts) == 1
    assert dagit_readonly_tls.hosts[0] == dagit_readonly_host
    assert dagit_readonly_tls.secret_name == dagit_readonly_tls_secret_name

    flower_tls = ingress.spec.tls[2]
    assert len(flower_tls.hosts) == 1
    assert flower_tls.hosts[0] == flower_host
    assert flower_tls.secret_name == flower_tls_secret_name
