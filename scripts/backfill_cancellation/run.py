"""Reproduce local source and optional private-wheel cancellation acceptance."""

import argparse
import email
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

SOURCE_PACKAGES = (
    "python_modules/dagster",
    "python_modules/dagster-graphql",
    "python_modules/dagster-test",
    "python_modules/dagster-pipes",
    "python_modules/libraries/dagster-shared",
    "python_modules/libraries/dagster-k8s",
    "python_modules/libraries/dagster-postgres",
    "python_modules/libraries/create-dagster",
    "python_modules/libraries/dagster-dg-core",
    "python_modules/libraries/dagster-cloud-cli",
)
RUNTIME_PACKAGES = (SOURCE_PACKAGES[0], SOURCE_PACKAGES[1], *SOURCE_PACKAGES[3:7])
TEST_TOOLS = (
    "pytest==9.1.1",
    "pytest-mock==3.16.0",
    "pytest-asyncio==1.4.0",
    "pytest-timeout==2.4.0",
    "responses==0.26.3",
    "syrupy==6.1.1",
    "mock==5.2.0",
    "psycopg2-binary==2.9.13",
    "psutil==7.2.2",
    "freezegun==1.5.5",
    "pytest-rerunfailures",
)
SUITES = (
    (
        "protocol",
        (
            "python_modules/dagster/dagster_tests/storage_tests/test_backfill_stop_protocol.py",
            "python_modules/dagster/dagster_tests/daemon_tests/test_backfill_stop_protocol.py",
            "python_modules/libraries/dagster-k8s/dagster_k8s_tests/unit_tests/test_backfill_worker_exit.py",
            "python_modules/libraries/dagster-k8s/dagster_k8s_tests/unit_tests/test_backfill_worker_dispatch.py",
            "python_modules/libraries/dagster-k8s/dagster_k8s_tests/unit_tests/test_backfill_pod_admission.py",
        ),
    ),
    (
        "storage-reexecution",
        (
            "python_modules/dagster/dagster_tests/storage_tests/test_run_storage.py",
            "python_modules/dagster/dagster_tests/core_tests/instance_tests/test_instance_reexecution.py",
        ),
    ),
    (
        "queue",
        (
            "python_modules/dagster/dagster_tests/daemon_tests/test_queued_run_coordinator_daemon.py",
        ),
    ),
    (
        "backfill",
        (
            "python_modules/dagster/dagster_tests/daemon_tests/test_backfill.py",
            "-k",
            "cancel or retry or retries",
        ),
    ),
    (
        "graphql-force-sync",
        (
            "python_modules/dagster-graphql/dagster_graphql_tests/graphql/test_backfill_stop_protocol.py",
        ),
    ),
)
POSTGRES_IMAGE = "postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--constraints", type=Path)
    parser.add_argument("--private-wheels", type=Path)
    parser.add_argument("--skip-unit", action="store_true")
    parser.add_argument(
        "--existing-kind-cluster",
        help="Reuse this local Kind cluster with task-owned namespaces only.",
    )
    args = parser.parse_args()
    if os.getenv("CI") == "true":
        parser.error("Worker acceptance must run locally, outside CI.")
    checkout = args.checkout.resolve(strict=True)
    assets = Path(__file__).resolve().parent
    root = Path(tempfile.mkdtemp(prefix="dagster-cancel-protocol-", dir="/tmp"))
    suffix = secrets.token_hex(4)
    cluster = args.existing_kind_cluster or "dagster-cancel-proof-" + suffix
    pg = "dagster-cancel-pg-" + suffix
    password = secrets.token_hex(24)
    result = {
        "started_at": time.time(),
        "cluster": cluster,
        "cluster_reused": args.existing_kind_cluster is not None,
        "postgres_container": pg,
        "checks": {},
        "errors": [],
    }
    print(f"Evidence directory: {root}", flush=True)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["KUBECONFIG"] = str(root / "kubeconfig")
    env["DAGSTER_HOME"] = str(root / "sandbox-instance")
    (root / "sandbox-instance").mkdir()
    (root / "sandbox-instance/dagster.yaml").write_text(
        "telemetry:\n  enabled: false\n", encoding="utf-8"
    )
    command_log = root / "commands.jsonl"

    def run(
        argv: list[str],
        name: str,
        *,
        require: bool = True,
        cwd: Path | None = None,
        run_env: dict | None = None,
    ) -> subprocess.CompletedProcess:
        with (root / (name + ".log")).open("w", encoding="utf-8") as output:
            completed = subprocess.run(
                argv,
                check=False,
                cwd=cwd,
                env=run_env or env,
                text=True,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=900,
            )
        with command_log.open("a", encoding="utf-8") as output:
            output.write(
                json.dumps(
                    {
                        "argv": argv,
                        "cwd": str(cwd) if cwd else None,
                        "exit_code": completed.returncode,
                    }
                )
                + "\n"
            )
        if require and completed.returncode:
            raise RuntimeError(
                f"{name} failed with exit {completed.returncode}; see {root / (name + '.log')}"
            )
        return completed

    def output(argv: list[str]) -> str:
        return subprocess.run(
            argv, check=True, capture_output=True, text=True, env=env, timeout=60
        ).stdout.strip()

    kube = ["kubectl", "--kubeconfig", str(root / "kubeconfig"), "--context", "kind-" + cluster]
    owned_resources: list[dict] = []

    def resource(kind: str, name: str) -> dict | None:
        completed = subprocess.run(
            kube + ["get", kind, name, "--ignore-not-found", "-o", "json"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        return json.loads(completed.stdout) if completed.stdout.strip() else None

    def cleanup_owned(reference: dict) -> None:
        data = resource(reference["kind"], reference["name"])
        if data is None:
            return
        if data["metadata"].get("labels", {}).get("dagster/qa-owner") != suffix:
            raise RuntimeError("Refusing to delete a resource without the task ownership label")
        if reference["kind"] != "namespace" and resource("namespace", reference["namespace"]):
            raise RuntimeError("Retaining admission configuration while its namespace still exists")
        run(
            kube + ["delete", reference["kind"], reference["name"], "--wait=true", "--timeout=60s"],
            reference["log_name"],
        )

    pg_started = False
    cluster_started = False
    try:
        (root / "source-revision.txt").write_text(
            output(["git", "-C", str(checkout), "rev-parse", "HEAD"]) + "\n", encoding="utf-8"
        )
        (root / "source-diff.patch").write_text(
            output(["git", "-C", str(checkout), "diff", "--binary", "HEAD"]) + "\n",
            encoding="utf-8",
        )
        run(["uv", "--no-config", "venv", "--python", "3.14.6", str(root / "venv")], "create-venv")
        python = str(root / "venv/bin/python")
        install = ["uv", "--no-config", "pip", "install", "--no-sources", "--python", python]
        if args.constraints:
            install += ["-c", str(args.constraints.resolve(strict=True))]
        for package in SOURCE_PACKAGES:
            install += ["-e", str(checkout / package)]
        run(install + list(TEST_TOOLS), "install")
        run(["uv", "--no-config", "pip", "freeze", "--python", python], "requirements-observed")
        constraints = root / "dependency-constraints.txt"
        constraints.write_text(
            args.constraints.read_text(encoding="utf-8")
            if args.constraints
            else output(
                [
                    python,
                    "-c",
                    "import importlib.metadata; print('\\n'.join(sorted(f'{d.metadata[\"Name\"]}=={d.version}' for d in importlib.metadata.distributions() if not d.read_text('direct_url.json'))))",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        if args.existing_kind_cluster:
            (root / "kubeconfig").write_text(
                output(["kind", "get", "kubeconfig", "--name", cluster]) + "\n", encoding="utf-8"
            )
            (root / "kubeconfig").chmod(0o600)
        else:
            cluster_started = True
            run(
                [
                    "kind",
                    "create",
                    "cluster",
                    "--name",
                    cluster,
                    "--kubeconfig",
                    str(root / "kubeconfig"),
                    "--image",
                    "kindest/node:v1.35.0@sha256:4613778f3cfcd10e615029370f5786704559103cf27bef934597ba562b269661",
                    "--wait",
                    "60s",
                ],
                "create-kind",
            )
        (root / "nodes.json").write_text(
            output(kube + ["get", "nodes", "-o", "json"]) + "\n", encoding="utf-8"
        )
        node_image = output(
            ["docker", "inspect", cluster + "-control-plane", "--format", "{{.Image}}"]
        )
        result["kind_node_image"] = output(
            ["docker", "image", "inspect", node_image, "--format", "{{.Id}} {{json .RepoDigests}}"]
        )
        pg_env = root / "postgres-docker.env"
        pg_env.write_text(
            "POSTGRES_DB=dagster_probe\nPOSTGRES_USER=dagster_probe\nPOSTGRES_PASSWORD="
            + password
            + "\n",
            encoding="utf-8",
        )
        pg_env.chmod(0o600)
        pg_started = True
        run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                pg,
                "--network",
                "kind",
                "--publish",
                "127.0.0.1::5432",
                "--env-file",
                str(pg_env),
                "--tmpfs",
                "/var/lib/postgresql/data",
                POSTGRES_IMAGE,
            ],
            "create-postgres",
        )
        deadline = time.monotonic() + 60
        while True:
            ready = subprocess.run(
                ["docker", "exec", pg, "pg_isready", "-U", "dagster_probe", "-d", "dagster_probe"],
                check=False,
                capture_output=True,
                env=env,
            )
            if ready.returncode == 0:
                break
            if time.monotonic() > deadline:
                raise TimeoutError("Disposable PostgreSQL did not become ready")
            time.sleep(0.2)
        port = output(["docker", "port", pg, "5432/tcp"]).rsplit(":", 1)[1]
        address = output(
            [
                "docker",
                "inspect",
                pg,
                "--format",
                '{{(index .NetworkSettings.Networks "kind").IPAddress}}',
            ]
        )
        local_url = f"postgresql+psycopg2://dagster_probe:{password}@127.0.0.1:{port}/dagster_probe"
        env["DAGSTER_TEST_POSTGRES_URL"] = local_url
        p = root / "postgres.env"
        p.write_text("export DAGSTER_TEST_POSTGRES_URL=" + local_url + "\n", encoding="utf-8")
        p.chmod(0o600)
        result["postgres_version"] = output(
            [
                "docker",
                "exec",
                pg,
                "psql",
                "-U",
                "dagster_probe",
                "-d",
                "dagster_probe",
                "-Atc",
                "SELECT version();",
            ]
        )
        if not args.skip_unit:
            for name, paths in SUITES:
                completed = run(
                    [
                        python,
                        "-m",
                        "pytest",
                        "--timeout",
                        "60",
                        "--force-reruns",
                        "0",
                        "-q",
                        "-o",
                        f"cache_dir={root / 'pytest-cache'}",
                        f"--junitxml={root / (name + '.xml')}",
                        *paths,
                    ],
                    name,
                    require=False,
                    cwd=checkout,
                )
                result["checks"][name] = completed.returncode
        completed = run(
            [
                python,
                str(assets / "native_probe.py"),
                str(root / "native-default"),
                "--expect-contained",
                "--allow-unproven-default-launcher",
                "--enable-stop-protocol",
            ],
            "native-default",
            require=False,
        )
        result["checks"]["native-default"] = completed.returncode

        for distribution, wheels in (("source", None), ("private-wheels", args.private_wheels)):
            if distribution == "private-wheels" and wheels is None:
                continue
            case = root / distribution
            case.mkdir()
            context = case / "image"
            context.mkdir()
            packages = context / "packages"
            packages.mkdir()
            if wheels is None:
                for relative in RUNTIME_PACKAGES:
                    source = checkout / relative
                    shutil.copytree(
                        source,
                        packages / source.name,
                        ignore=shutil.ignore_patterns(
                            "__pycache__",
                            ".pytest_cache",
                            ".venv",
                            "dagster_tests",
                            "dagster_k8s_tests",
                            "dagster_postgres_tests",
                        ),
                    )
                shutil.copy2(checkout / ".gitignore", packages / ".gitignore")
                runtime_requirements = ""
            else:
                wheel_paths = sorted(wheels.resolve(strict=True).glob("*.whl"))
                if not wheel_paths:
                    raise ValueError("--private-wheels directory contains no wheels")
                for path in wheel_paths:
                    shutil.copy2(path, packages / path.name)
                versions = {}
                for path in wheel_paths:
                    with zipfile.ZipFile(path) as wheel:
                        metadata_path = next(
                            name
                            for name in wheel.namelist()
                            if name.endswith(".dist-info/METADATA")
                        )
                        metadata = email.message_from_bytes(wheel.read(metadata_path))
                        versions[metadata["Name"]] = metadata["Version"].split("+", 1)[0]
                core_version = versions["dagster"]
                k8s_version = versions["dagster-k8s"]
                runtime_requirements = (
                    f"dagster-graphql=={core_version}\ndagster-pipes=={core_version}\n"
                    f"dagster-shared=={core_version}\ndagster-postgres=={k8s_version}\n"
                )
            for name in (
                "Dockerfile",
                "cancel_k8s_fixture.py",
                "k8s_cancel_probe.py",
                "admission_probe_server.py",
            ):
                shutil.copy2(assets / name, context / name)
            shutil.copy2(constraints, context / "dependency-constraints.txt")
            (context / "runtime-requirements.txt").write_text(
                runtime_requirements, encoding="utf-8"
            )
            manifest = {
                str(path.relative_to(context)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(context.rglob("*"))
                if path.is_file()
            }
            (case / "image-input-hashes.json").write_text(
                json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
            image = "dagster-cancel-proof:" + distribution + "-" + suffix
            run(["docker", "build", "--check", str(context)], distribution + "-build-check")
            run(["docker", "build", "--tag", image, str(context)], distribution + "-build")
            (case / "image-id.txt").write_text(
                output(
                    [
                        "docker",
                        "image",
                        "inspect",
                        image,
                        "--format",
                        "{{.Id}} {{json .RepoDigests}}",
                    ]
                ),
                encoding="utf-8",
            )
            run(
                ["kind", "load", "docker-image", image, "--name", cluster],
                distribution + "-load-image",
            )
            for mode in ("normal", "held-before", "held-after"):
                label = distribution + "-" + mode
                namespace = "dagster-cancel-" + suffix + "-" + label
                webhook_name = "dagster-qa-" + suffix + "-" + label
                references = [
                    {
                        "kind": kind,
                        "name": name,
                        "namespace": namespace,
                        "log_name": label + "-cleanup-" + kind,
                    }
                    for kind, name in (
                        ("namespace", namespace),
                        ("mutatingwebhookconfiguration", webhook_name),
                        ("clusterrolebinding", webhook_name + "-reader"),
                        ("clusterrole", webhook_name + "-reader"),
                    )
                ]
                for reference in references:
                    if resource(reference["kind"], reference["name"]) is not None:
                        raise RuntimeError(
                            "Generated QA resource already exists; refusing to change it"
                        )
                owned_resources.extend(references)
                probe = case / mode
                probe.mkdir()
                database = "dagster_probe_" + label.replace("-", "_") + "_" + suffix
                run(
                    [
                        "docker",
                        "exec",
                        pg,
                        "psql",
                        "-U",
                        "dagster_probe",
                        "-d",
                        "dagster_probe",
                        "-c",
                        f'CREATE DATABASE "{database}"',
                    ],
                    label + "-database",
                )
                kind_case = probe / "kind"
                kind_case.mkdir()
                shutil.copy2(root / "postgres.env", probe / "postgres.env")
                (kind_case / "postgres-address.txt").write_text(address + "\n", encoding="utf-8")
                (kind_case / "database.json").write_text(
                    json.dumps({"database": database}), encoding="utf-8"
                )
                asset_env = {**env, "PYTHONPATH": str(assets)}
                run(
                    [
                        python,
                        str(assets / "prepare_controller.py"),
                        str(kind_case),
                        image,
                        "--case",
                        mode,
                        "--namespace",
                        namespace,
                        "--webhook-name",
                        webhook_name,
                        "--owner",
                        suffix,
                    ],
                    label + "-prepare-controller",
                    run_env=asset_env,
                )
                run(
                    kube + ["apply", "-f", str(kind_case / "controller.yaml")],
                    label + "-apply-controller",
                )
                run(
                    kube
                    + [
                        "-n",
                        namespace,
                        "wait",
                        "--for=condition=Ready",
                        "pod/controller",
                        "--timeout=90s",
                    ],
                    label + "-wait-controller",
                    require=False,
                )
                run(
                    kube + ["-n", namespace, "logs", "--follow", "controller"],
                    label + "-controller",
                )
                run(
                    kube + ["-n", namespace, "logs", "admission"],
                    label + "-admission",
                    require=False,
                )
                text = (root / (label + "-controller.log")).read_text(encoding="utf-8")
                records = [
                    line.removeprefix("DAGSTER_CANCEL_EVIDENCE=")
                    for line in text.splitlines()
                    if line.startswith("DAGSTER_CANCEL_EVIDENCE=")
                ]
                data = (
                    json.loads(records[-1])
                    if records
                    else {"fully_stopped": False, "error": "Controller did not emit evidence"}
                )
                (probe / "result.json").write_text(
                    json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8"
                )
                result["checks"][label + "-kind"] = 0 if data.get("fully_stopped") else 1
                node = cluster + "-control-plane"
                cri = json.loads(
                    output(["docker", "exec", node, "crictl", "ps", "--all", "--output", "json"])
                )
                workers = [
                    {
                        "id": c["id"],
                        "state": c.get("state"),
                        "pod_uid": c.get("labels", {}).get("io.kubernetes.pod.uid"),
                        "pod_name": c.get("labels", {}).get("io.kubernetes.pod.name"),
                    }
                    for c in cri.get("containers", [])
                    if c.get("labels", {}).get("io.kubernetes.pod.namespace") == namespace
                    and c.get("labels", {}).get("io.kubernetes.pod.name")
                    not in ("controller", "admission")
                ]
                (probe / "runtime-worker-containers.json").write_text(
                    json.dumps(workers, indent=2) + "\n", encoding="utf-8"
                )
                if any(c["state"] == "CONTAINER_RUNNING" for c in workers):
                    result["checks"][label + "-kind"] = 1
                (probe / "owned-resources.json").write_text(
                    json.dumps(references, indent=2) + "\n", encoding="utf-8"
                )
                for reference in references:
                    cleanup_owned(reference)
    except Exception as error:
        result["errors"].append(str(error))
        print(str(error), flush=True)
    finally:
        for reference in owned_resources:
            try:
                cleanup_owned(reference)
            except Exception as error:
                result["errors"].append(str(error))
        if cluster_started:
            run(
                [
                    "kind",
                    "delete",
                    "cluster",
                    "--name",
                    cluster,
                    "--kubeconfig",
                    str(root / "kubeconfig"),
                ],
                "cleanup-kind",
                require=False,
            )
        remaining_resources = (
            [
                reference
                for reference in owned_resources
                if resource(reference["kind"], reference["name"]) is not None
            ]
            if args.existing_kind_cluster
            else []
        )
        if pg_started:
            run(["docker", "logs", pg], "postgres", require=False)
            if remaining_resources:
                result["errors"].append(
                    "Retained PostgreSQL because reused-cluster fixture resources did not drain"
                )
            else:
                run(["docker", "rm", "--force", pg], "cleanup-postgres", require=False)
        result["remaining_owned_clusters"] = (
            []
            if args.existing_kind_cluster
            else [
                name for name in output(["kind", "get", "clusters"]).splitlines() if name == cluster
            ]
        )
        result["reused_cluster_present_after"] = (
            cluster in output(["kind", "get", "clusters"]).splitlines()
            if args.existing_kind_cluster
            else None
        )
        result["remaining_owned_resources"] = remaining_resources
        result["remaining_owned_containers"] = output(
            ["docker", "ps", "--all", "--filter", f"name=^{pg}$", "--format", "{{.ID}}"]
        )
        result["elapsed_seconds"] = time.time() - result["started_at"]
        (root / "summary.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        public = root / "publication-evidence"
        public.mkdir()
        allowed_root = {
            "commands.jsonl",
            "summary.json",
            "source-revision.txt",
            "source-diff.patch",
            "requirements-observed.log",
            "dependency-constraints.txt",
            "nodes.json",
            *(
                name + suffix
                for name in (
                    "create-venv",
                    "install",
                    "create-kind",
                    "create-postgres",
                    "native-default",
                    "cleanup-kind",
                    "cleanup-postgres",
                    "postgres",
                )
                for suffix in (".log",)
            ),
            *(name + suffix for name, _ in SUITES for suffix in (".log", ".xml")),
            *(
                distribution + "-" + mode + suffix
                for distribution in ("source", "private-wheels")
                for mode in ("normal", "held-before", "held-after")
                for suffix in (
                    "-database.log",
                    "-prepare-controller.log",
                    "-apply-controller.log",
                    "-wait-controller.log",
                    "-controller.log",
                    "-admission.log",
                    "-cleanup-namespace.log",
                    "-cleanup-mutatingwebhookconfiguration.log",
                    "-cleanup-clusterrolebinding.log",
                    "-cleanup-clusterrole.log",
                )
            ),
            *(
                distribution + suffix
                for distribution in ("source", "private-wheels")
                for suffix in (
                    "-build-check.log",
                    "-build.log",
                    "-load-image.log",
                    "-database.log",
                    "-prepare-controller.log",
                    "-apply-controller.log",
                    "-wait-controller.log",
                    "-controller.log",
                    "-namespace-cleanup.log",
                )
            ),
        }
        allowed_nested = {
            "result.json",
            "image-input-hashes.json",
            "image-id.txt",
            "runtime-worker-containers.json",
            "native-events.jsonl",
            "processes.json",
            "owned-resources.json",
        }
        for path in root.rglob("*"):
            relative = path.relative_to(root)
            if not path.is_file() or not (
                (len(relative.parts) == 1 and path.name in allowed_root)
                or (
                    relative.parts[0] in {"source", "private-wheels", "native-default"}
                    and path.name in allowed_nested
                    and "image" not in relative.parts
                )
            ):
                continue
            text = path.read_text(encoding="utf-8").replace(
                password, "[REDACTED_DISPOSABLE_POSTGRES_PASSWORD]"
            )
            target = public / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        print(
            json.dumps({"evidence": str(root), "publication_evidence": str(public), **result}),
            flush=True,
        )
    return (
        1
        if result["errors"]
        or any(result["checks"].values())
        or result["remaining_owned_clusters"]
        or result["remaining_owned_containers"]
        or result["remaining_owned_resources"]
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
