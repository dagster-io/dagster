from enum import Enum
from typing import Any

from pydantic import BaseModel

from schema.charts.utils import kubernetes


class HTTPRoutePathType(str, Enum):
    EXACT = "Exact"
    PATH_PREFIX = "PathPrefix"
    REGULAR_EXPRESSION = "RegularExpression"


# See https://gateway-api.sigs.k8s.io/reference/spec/#parentreference
class HTTPRouteParentReference(BaseModel, extra="allow"):
    name: str


# See https://gateway-api.sigs.k8s.io/reference/spec/#httproutetimeouts
class HTTPRouteTimeouts(BaseModel, extra="forbid"):
    request: str | None = None
    backendRequest: str | None = None


class HTTPRouteConfiguration(BaseModel):
    hostnames: list[str]
    parentRefs: list[HTTPRouteParentReference]
    path: str
    pathType: HTTPRoutePathType
    filters: list[dict[str, Any]]
    timeouts: HTTPRouteTimeouts
    additionalRules: list[dict[str, Any]]


class HTTPRoute(BaseModel):
    enabled: bool
    labels: kubernetes.Labels
    annotations: kubernetes.Annotations
    parentRefs: list[HTTPRouteParentReference]
    flower: HTTPRouteConfiguration
    dagsterWebserver: HTTPRouteConfiguration
    readOnlyDagsterWebserver: HTTPRouteConfiguration
