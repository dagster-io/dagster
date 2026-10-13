"""Write manifests for the explicitly isolated local Kind cancellation probe."""

import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import yaml
from k8s_cancel_probe import instance_config


def main(root: Path, image: str) -> None:
    namespace = "cancellation-proof"
    local_root = root.parent
    url = (local_root / "postgres.env").read_text(encoding="utf-8").strip().split("=", 1)[1]
    address = (root / "postgres-address.txt").read_text(encoding="utf-8").strip()
    database = json.loads((root / "database.json").read_text(encoding="utf-8"))["database"]
    parsed = urlsplit(url)
    # Dagster Postgres declares psycopg2-binary. SQLAlchemy 2.1 uses psycopg for
    # bare postgresql URLs, so select the installed driver explicitly.
    in_cluster_url = urlunsplit(
        (
            "postgresql+psycopg2",
            f"{parsed.username}:{parsed.password}@{address}:5432",
            "/" + database,
            "",
            "",
        )
    )
    resources = [
        {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": namespace}},
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "dagster-worker", "namespace": namespace},
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {"name": "dagster-worker", "namespace": namespace},
            "rules": [
                {
                    "apiGroups": ["batch"],
                    "resources": ["jobs"],
                    "verbs": ["create", "get", "list", "watch", "delete"],
                },
                {
                    "apiGroups": [""],
                    "resources": ["pods", "pods/log"],
                    "verbs": ["create", "get", "list", "watch", "delete"],
                },
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {"name": "dagster-worker", "namespace": namespace},
            "subjects": [
                {"kind": "ServiceAccount", "name": "dagster-worker", "namespace": namespace}
            ],
            "roleRef": {
                "kind": "Role",
                "name": "dagster-worker",
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "dagster-instance", "namespace": namespace},
            "data": {"dagster.yaml": yaml.safe_dump(instance_config(namespace, image))},
        },
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "dagster-probe-env", "namespace": namespace},
            "stringData": {
                "DAGSTER_POSTGRES_URL": in_cluster_url,
                "PROBE_IMAGE": image,
                "PROBE_NAMESPACE": namespace,
                "DAGSTER_CURRENT_IMAGE": image,
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "controller", "namespace": namespace},
            "spec": {
                "serviceAccountName": "dagster-worker",
                "restartPolicy": "Never",
                "containers": [
                    {
                        "name": "controller",
                        "image": image,
                        "imagePullPolicy": "Never",
                        "command": ["python", "/opt/probe/k8s_cancel_probe.py"],
                        "envFrom": [{"secretRef": {"name": "dagster-probe-env"}}],
                    }
                ],
            },
        },
    ]
    path = root / "controller.yaml"
    path.write_text(yaml.safe_dump_all(resources), encoding="utf-8")
    path.chmod(0o600)
    print(path)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
