import subprocess

import pytest
from schema.charts.dagster.subschema.flower import Flower
from schema.charts.dagster.subschema.http_route import (
    HTTPRoute,
    HTTPRouteConfiguration,
    HTTPRouteParentReference,
    HTTPRoutePathType,
    HTTPRouteTimeouts,
)
from schema.charts.dagster.subschema.webserver import Webserver
from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.utils import kubernetes
from schema.utils.helm_template import HelmTemplate


# HTTPRoute is a custom resource, so there is no model in the Kubernetes client to deserialize to.
@pytest.fixture(name="template")
def helm_template() -> HelmTemplate:
    return HelmTemplate(
        helm_dir_path="helm/dagster",
        subchart_paths=["charts/dagster-user-deployments"],
        output="templates/httproute.yaml",
    )


def test_http_route_disabled_by_default(template: HelmTemplate):
    with pytest.raises(subprocess.CalledProcessError):
        template.render(DagsterHelmValues.construct())


def test_http_route(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[
                HTTPRouteParentReference(name="gateway", namespace="infra", sectionName="https")  # type: ignore
            ],
            dagsterWebserver=HTTPRouteConfiguration.construct(
                hostnames=["foobar.com"],
            ),
        )
    )

    [http_route] = template.render(helm_values)

    assert http_route["apiVersion"] == "gateway.networking.k8s.io/v1"
    assert http_route["kind"] == "HTTPRoute"
    assert http_route["metadata"]["name"] == "release-name-dagster-webserver"
    assert http_route["spec"]["parentRefs"] == [
        {"name": "gateway", "namespace": "infra", "sectionName": "https"}
    ]
    assert http_route["spec"]["hostnames"] == ["foobar.com"]
    assert http_route["spec"]["rules"] == [
        {
            "matches": [{"path": {"type": "PathPrefix", "value": "/"}}],
            "backendRefs": [{"name": "release-name-dagster-webserver", "port": 80}],
        }
    ]


def test_http_route_without_hostnames(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[HTTPRouteParentReference(name="gateway")],
        )
    )

    [http_route] = template.render(helm_values)

    assert "hostnames" not in http_route["spec"]


def test_http_route_requires_parent_refs(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(httpRoute=HTTPRoute.construct(enabled=True))

    with pytest.raises(subprocess.CalledProcessError):
        template.render(helm_values)


def test_http_route_rule(template: HelmTemplate):
    filters = [
        {
            "type": "RequestHeaderModifier",
            "requestHeaderModifier": {"set": [{"name": "X-Forwarded-Proto", "value": "https"}]},
        }
    ]
    additional_rules = [
        {
            "matches": [{"path": {"type": "Exact", "value": "/other"}}],
            "backendRefs": [{"name": "other-service", "port": 8080}],
        }
    ]
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[HTTPRouteParentReference(name="gateway")],
            dagsterWebserver=HTTPRouteConfiguration.construct(
                path="/dagster",
                pathType=HTTPRoutePathType.EXACT,
                filters=filters,
                timeouts=HTTPRouteTimeouts(request="60s", backendRequest="30s"),
                additionalRules=additional_rules,
            ),
        ),
        dagsterWebserver=Webserver.construct(
            service=kubernetes.Service(type="ClusterIP", port=3000)
        ),
    )

    [http_route] = template.render(helm_values)

    assert http_route["spec"]["rules"] == [
        {
            "matches": [{"path": {"type": "Exact", "value": "/dagster"}}],
            "filters": filters,
            "backendRefs": [{"name": "release-name-dagster-webserver", "port": 3000}],
            "timeouts": {"request": "60s", "backendRequest": "30s"},
        },
        *additional_rules,
    ]


def test_http_route_read_only(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[HTTPRouteParentReference(name="gateway")],
            dagsterWebserver=HTTPRouteConfiguration.construct(hostnames=["foobar.com"]),
            readOnlyDagsterWebserver=HTTPRouteConfiguration.construct(
                hostnames=["dagster.io"],
                parentRefs=[HTTPRouteParentReference(name="internal-gateway")],
            ),
        ),
        dagsterWebserver=Webserver.construct(enableReadOnly=True),
    )

    webserver_http_route, read_only_http_route = template.render(helm_values)

    assert webserver_http_route["metadata"]["name"] == "release-name-dagster-webserver"
    assert webserver_http_route["spec"]["parentRefs"] == [{"name": "gateway"}]
    assert webserver_http_route["spec"]["hostnames"] == ["foobar.com"]

    read_only_name = "release-name-dagster-webserver-read-only"
    assert read_only_http_route["metadata"]["name"] == read_only_name
    assert read_only_http_route["spec"]["parentRefs"] == [{"name": "internal-gateway"}]
    assert read_only_http_route["spec"]["hostnames"] == ["dagster.io"]
    assert read_only_http_route["spec"]["rules"][0]["backendRefs"] == [
        {"name": read_only_name, "port": 80}
    ]


def test_http_route_flower(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[HTTPRouteParentReference(name="gateway")],
            flower=HTTPRouteConfiguration.construct(hostnames=["flower.com"], path="/flower"),
        ),
        flower=Flower.construct(enabled=True),
    )

    _, flower_http_route = template.render(helm_values)

    assert flower_http_route["metadata"]["name"] == "release-name-flower"
    assert flower_http_route["spec"]["hostnames"] == ["flower.com"]
    assert flower_http_route["spec"]["rules"] == [
        {
            "matches": [{"path": {"type": "PathPrefix", "value": "/flower"}}],
            "backendRefs": [{"name": "release-name-dagster-flower-service", "port": 5555}],
        }
    ]


def test_http_route_labels_and_annotations(template: HelmTemplate):
    helm_values = DagsterHelmValues.construct(
        httpRoute=HTTPRoute.construct(
            enabled=True,
            parentRefs=[HTTPRouteParentReference(name="gateway")],
            labels={"foo": "bar"},
            annotations={"baz": "qux"},
        )
    )

    [http_route] = template.render(helm_values)

    assert http_route["metadata"]["labels"]["foo"] == "bar"
    assert http_route["metadata"]["annotations"]["baz"] == "qux"
