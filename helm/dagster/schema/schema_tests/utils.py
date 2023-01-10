from typing import Optional

from schema.charts.dagster_user_deployments.subschema.user_deployments import (
    UserDeployment,
    UserDeploymentIncludeConfigInLaunchedRuns,
)
from schema.charts.utils import kubernetes


def create_simple_user_deployment(
    name: str, include_config_in_launched_runs: Optional[bool] = None
) -> UserDeployment:
    return UserDeployment(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        includeConfigInLaunchedRuns=(
            UserDeploymentIncludeConfigInLaunchedRuns(enabled=include_config_in_launched_runs)
            if include_config_in_launched_runs is not None
            else None
        ),
    )


def create_complex_user_deployment(
    name: str, include_config_in_launched_runs: bool = False
) -> UserDeployment:
    return UserDeployment(
        name=name,
        image=kubernetes.Image(repository=f"repo/{name}", tag="tag1", pullPolicy="Always"),
        dagsterApiGrpcArgs=["-m", name],
        port=3030,
        annotations=kubernetes.Annotations.parse_obj(
            {"annotation_1": "an_annotation_1", "annotation_2": "an_annotation_2"}
        ),
        nodeSelector=kubernetes.NodeSelector.parse_obj(
            {"node_selector_1": "node_type_1", "node_selector_2": "node_type_2"}
        ),
        affinity=kubernetes.Affinity.parse_obj(
            {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [
                            {
                                "matchExpressions": [
                                    {
                                        "key": "kubernetes.io/e2e-az-name",
                                        "operator": "In",
                                        "values": ["e2e-az1", "e2e-az2"],
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        ),
        tolerations=kubernetes.Tolerations.parse_obj(
            [{"key": "key1", "operator": "Exists", "effect": "NoSchedule"}]
        ),
        podSecurityContext=kubernetes.PodSecurityContext.parse_obj(
            {"runAsUser": 1000, "runAsGroup": 3000}
        ),
        securityContext=kubernetes.SecurityContext.parse_obj(
            {"runAsUser": 1000, "runAsGroup": 3000}
        ),
        resources=kubernetes.Resources.parse_obj(
            {
                "requests": {"memory": "64Mi", "cpu": "250m"},
                "limits": {"memory": "128Mi", "cpu": "500m"},
            }
        ),
        labels={
            "label_one": "one",
            "label_two": "two",
        },
        includeConfigInLaunchedRuns=UserDeploymentIncludeConfigInLaunchedRuns(
            enabled=include_config_in_launched_runs
        ),
    )
