import pytest
from kubernetes.client import models
from schema.charts.dagster.subschema.ingress import (
    FlowerIngressConfiguration,
    Ingress,
    IngressPath,
    IngressPathType,
    IngressTLSConfiguration,
    WebserverIngressConfiguration,
)
from schema.charts.dagster.subschema.webserver import Webserver
from schema.charts.dagster.values import DagsterHelmValues
from schema.utils.helm_template import HelmTemplate


@pytest.fixture(name="template_function")
def helm_template_function():
    return lambda output, model: HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output=output,
        model=model,
    )


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("webserver_field", ["dagsterWebserver", "dagit"])
@pytest.mark.parametrize(
    argnames=["output", "model", "api_version"],
    argvalues=[
        (
            "templates/ingress-v1beta1.yaml",
            models.ExtensionsV1beta1Ingress,
            "extensions/v1beta1/Ingress",
        ),
        (
            "templates/ingress.yaml",
            models.V1Ingress,
            "networking.k8s.io/v1/Ingress",
        ),
    ],
)
def test_ingress(template_function, webserver_field, output, model, api_version):
    webserver_kwargs = {
        webserver_field: WebserverIngressConfiguration.construct(
            host="foobar.com",
            path="bing",
            pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
            precedingPaths=[
                IngressPath(
                    path="/*",
                    pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                    serviceName="ssl-redirect",
                    servicePort="use-annotion",
                )
            ],
        )
    }

    template = template_function(output, model)
    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            apiVersion=api_version,
            **webserver_kwargs,  # type: ignore
        )
    )

    ingress_template = template.render(helm_values)
    assert len(ingress_template) == 1
    ingress = ingress_template[0]

    assert len(ingress.spec.rules) == 1
    rule = ingress.spec.rules[0]

    assert rule.host == "foobar.com"


# Parametrizing "webserver_field" here tests backcompat. `dagit` was the old field name.
# This parametrization can be removed in 2.0.
@pytest.mark.parametrize("readonly_webserver_field", ["readOnlyDagsterWebserver", "readOnlyDagit"])
@pytest.mark.parametrize(
    argnames=["output", "model", "api_version"],
    argvalues=[
        (
            "templates/ingress-v1beta1.yaml",
            models.ExtensionsV1beta1Ingress,
            "extensions/v1beta1/Ingress",
        ),
        (
            "templates/ingress.yaml",
            models.V1Ingress,
            "networking.k8s.io/v1/Ingress",
        ),
    ],
)
def test_ingress_read_only(template_function, readonly_webserver_field, output, model, api_version):
    template = template_function(output, model)
    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            apiVersion=api_version,
            dagsterWebserver=WebserverIngressConfiguration.construct(
                host="foobar.com",
                path="bing",
                pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                precedingPaths=[
                    IngressPath(
                        path="/*",
                        pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                        serviceName="ssl-redirect",
                        servicePort="use-annotion",
                    )
                ],
            ),
            **{
                readonly_webserver_field: WebserverIngressConfiguration.construct(
                    host="dagster.io",
                    succeedingPaths=[
                        IngressPath(
                            path="/*",
                            pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                            serviceName="ssl-redirect",
                            servicePort="use-annotion",
                        )
                    ],
                ),
            },
        ),
        dagsterWebserver=Webserver.construct(enableReadOnly=True),
    )

    ingress_template = template.render(helm_values)
    assert len(ingress_template) == 1
    ingress = ingress_template[0]

    assert len(ingress.spec.rules) == 2
    assert [rule.host for rule in ingress.spec.rules] == ["foobar.com", "dagster.io"]


@pytest.mark.parametrize(
    argnames=["output", "model", "api_version"],
    argvalues=[
        (
            "templates/ingress-v1beta1.yaml",
            models.ExtensionsV1beta1Ingress,
            "extensions/v1beta1/Ingress",
        ),
        (
            "templates/ingress.yaml",
            models.V1Ingress,
            "networking.k8s.io/v1/Ingress",
        ),
    ],
)
def test_ingress_tls(template_function, output, model, api_version):
    template = template_function(output, model)
    webserver_host = "webserver.com"
    webserver_readonly_host = "webserver-readonly.com"
    flower_host = "flower.com"

    webserver_tls_secret_name = "webserver_tls_secret_name"
    webserver_readonly_tls_secret_name = "webserver_readonly_tls_secret_name"
    flower_tls_secret_name = "flower_tls_secret_name"

    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            apiVersion=api_version,
            dagsterWebserver=WebserverIngressConfiguration.construct(
                host=webserver_host,
                pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                tls=IngressTLSConfiguration(enabled=True, secretName=webserver_tls_secret_name),
            ),
            readOnlyDagsterWebserver=WebserverIngressConfiguration.construct(
                host=webserver_readonly_host,
                pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                tls=IngressTLSConfiguration(
                    enabled=True, secretName=webserver_readonly_tls_secret_name
                ),
            ),
            flower=FlowerIngressConfiguration.construct(
                host=flower_host,
                pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                tls=IngressTLSConfiguration(enabled=True, secretName=flower_tls_secret_name),
            ),
        ),
        dagsterWebserver=Webserver.construct(enableReadOnly=True),
    )

    [ingress] = template.render(helm_values)

    assert len(ingress.spec.tls) == 3

    webserver_tls = ingress.spec.tls[0]
    assert len(webserver_tls.hosts) == 1
    assert webserver_tls.hosts[0] == webserver_host
    assert webserver_tls.secret_name == webserver_tls_secret_name

    webserver_readonly_tls = ingress.spec.tls[1]
    assert len(webserver_readonly_tls.hosts) == 1
    assert webserver_readonly_tls.hosts[0] == webserver_readonly_host
    assert webserver_readonly_tls.secret_name == webserver_readonly_tls_secret_name

    flower_tls = ingress.spec.tls[2]
    assert len(flower_tls.hosts) == 1
    assert flower_tls.hosts[0] == flower_host
    assert flower_tls.secret_name == flower_tls_secret_name


@pytest.mark.parametrize(
    argnames=["output", "model", "api_version"],
    argvalues=[
        (
            "templates/ingress-v1beta1.yaml",
            models.ExtensionsV1beta1Ingress,
            "extensions/v1beta1/Ingress",
        ),
        (
            "templates/ingress.yaml",
            models.V1Ingress,
            "networking.k8s.io/v1/Ingress",
        ),
    ],
)
def test_ingress_labels(template_function, output, model, api_version):
    template = template_function(output, model)
    helm_values = DagsterHelmValues.construct(
        ingress=Ingress.construct(
            enabled=True,
            apiVersion=api_version,
            dagsterWebserver=WebserverIngressConfiguration.construct(
                host="foobar.com",
                path="bing",
                pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                precedingPaths=[
                    IngressPath(
                        path="/*",
                        pathType=IngressPathType.IMPLEMENTATION_SPECIFIC,
                        serviceName="ssl-redirect",
                        servicePort="use-annotion",
                    )
                ],
            ),
            labels={"foo": "bar"},
        )
    )

    ingress_template = template.render(helm_values)
    assert len(ingress_template) == 1
    ingress = ingress_template[0]

    assert ingress.metadata.labels["foo"] == "bar"
