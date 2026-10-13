"""Write isolated local Kind fixtures for native Jobs and durable Pod admission."""

import argparse
import base64
import datetime
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import yaml
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION
from dagster_k8s.backfill_admission import (
    ADMISSION_ROUTE_LABEL,
    ADMISSION_WEBHOOK_NAME,
    WEBHOOK_CONTRACT_ANNOTATION,
)
from k8s_cancel_probe import instance_config

SERVICE = "dagster-admission"


def certificates(namespace: str) -> dict[str, str]:
    now = datetime.datetime.now(datetime.UTC)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "local-dagster-qa-ca")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=2))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    dns = f"{SERVICE}.{namespace}.svc"
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, SERVICE)]))
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=2))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(dns), x509.DNSName(dns + ".cluster.local")]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    return {
        "ca.crt": ca.public_bytes(serialization.Encoding.PEM).decode(),
        "tls.crt": cert.public_bytes(serialization.Encoding.PEM).decode(),
        "tls.key": key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode(),
    }


def main(root: Path, image: str, case: str, namespace: str, webhook_name: str, owner: str) -> None:
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
    tls = certificates(namespace)
    role = webhook_name + "-reader"
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
                    "verbs": ["create", "get", "list", "watch", "delete", "patch"],
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
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRole",
            "metadata": {"name": role},
            "rules": [
                {
                    "apiGroups": ["admissionregistration.k8s.io"],
                    "resources": ["mutatingwebhookconfigurations"],
                    "resourceNames": [webhook_name],
                    "verbs": ["get"],
                }
            ],
        },
        {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "ClusterRoleBinding",
            "metadata": {"name": role},
            "subjects": [
                {"kind": "ServiceAccount", "name": "dagster-worker", "namespace": namespace}
            ],
            "roleRef": {
                "kind": "ClusterRole",
                "name": role,
                "apiGroup": "rbac.authorization.k8s.io",
            },
        },
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "dagster-instance", "namespace": namespace},
            "data": {
                "dagster.yaml": yaml.safe_dump(instance_config(namespace, image, webhook_name))
            },
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
                "PROBE_CASE": case,
                "PROBE_ADMISSION_WEBHOOK_NAME": webhook_name,
                "PROBE_ADMISSION_URL": f"https://{SERVICE}.{namespace}.svc",
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "dagster-admission-tls", "namespace": namespace},
            "type": "kubernetes.io/tls",
            "stringData": {"tls.crt": tls["tls.crt"], "tls.key": tls["tls.key"]},
        },
        {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "dagster-admission-ca", "namespace": namespace},
            "data": {"ca.crt": tls["ca.crt"]},
        },
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": SERVICE, "namespace": namespace},
            "spec": {
                "selector": {"app": "dagster-admission"},
                "ports": [{"port": 443, "targetPort": 8443}],
            },
        },
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "admission",
                "namespace": namespace,
                "labels": {"app": "dagster-admission"},
            },
            "spec": {
                "serviceAccountName": "dagster-worker",
                "restartPolicy": "Never",
                "containers": [
                    {
                        "name": "admission",
                        "image": image,
                        "imagePullPolicy": "Never",
                        "command": [
                            "python",
                            "/opt/probe/admission_probe_server.py",
                            "--tls-cert",
                            "/certs/tls.crt",
                            "--tls-key",
                            "/certs/tls.key",
                            "--mode",
                            case,
                            "--webhook-name",
                            webhook_name,
                        ],
                        "envFrom": [{"secretRef": {"name": "dagster-probe-env"}}],
                        "env": [{"name": "DAGSTER_HOME", "value": "/opt/dagster/dagster_home"}],
                        "volumeMounts": [
                            {"name": "tls", "mountPath": "/certs", "readOnly": True},
                            {
                                "name": "instance",
                                "mountPath": "/opt/dagster/dagster_home/dagster.yaml",
                                "subPath": "dagster.yaml",
                                "readOnly": True,
                            },
                        ],
                        "readinessProbe": {
                            "httpGet": {"path": "/healthz", "port": 8443, "scheme": "HTTPS"},
                            "periodSeconds": 1,
                        },
                    }
                ],
                "volumes": [
                    {"name": "tls", "secret": {"secretName": "dagster-admission-tls"}},
                    {"name": "instance", "configMap": {"name": "dagster-instance"}},
                ],
            },
        },
        {
            "apiVersion": "admissionregistration.k8s.io/v1",
            "kind": "MutatingWebhookConfiguration",
            "metadata": {
                "name": webhook_name,
                "annotations": {WEBHOOK_CONTRACT_ANNOTATION: BACKFILL_STOP_PROTOCOL_VERSION},
            },
            "webhooks": [
                {
                    "name": "backfill-pods.dagster.io",
                    "admissionReviewVersions": ["v1"],
                    "sideEffects": "NoneOnDryRun",
                    "failurePolicy": "Fail",
                    "reinvocationPolicy": "Never",
                    "timeoutSeconds": 30,
                    "objectSelector": {"matchLabels": {ADMISSION_ROUTE_LABEL: webhook_name}},
                    "rules": [
                        {
                            "apiGroups": [""],
                            "apiVersions": ["v1"],
                            "operations": ["CREATE"],
                            "resources": ["pods"],
                            "scope": "Namespaced",
                        }
                    ],
                    "clientConfig": {
                        "service": {
                            "name": SERVICE,
                            "namespace": namespace,
                            "path": "/admit",
                            "port": 443,
                        },
                        "caBundle": base64.b64encode(tls["ca.crt"].encode()).decode(),
                    },
                }
            ],
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
                        "volumeMounts": [{"name": "ca", "mountPath": "/certs", "readOnly": True}],
                    }
                ],
                "volumes": [{"name": "ca", "configMap": {"name": "dagster-admission-ca"}}],
            },
        },
    ]
    for resource in resources:
        resource["metadata"].setdefault("labels", {})["dagster/qa-owner"] = owner
    path = root / "controller.yaml"
    path.write_text(yaml.safe_dump_all(resources), encoding="utf-8")
    path.chmod(0o600)
    print(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("image")
    parser.add_argument("--case", choices=("normal", "held-before", "held-after"), default="normal")
    parser.add_argument("--namespace", default="cancellation-proof")
    parser.add_argument("--webhook-name", default=ADMISSION_WEBHOOK_NAME)
    parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    main(args.root, args.image, args.case, args.namespace, args.webhook_name, args.owner)
