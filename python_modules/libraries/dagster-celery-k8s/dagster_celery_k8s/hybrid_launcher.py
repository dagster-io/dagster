# isort: skip_file

import hashlib
import json
import os
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from dagster import DagsterInstance, Field, Permissive, StringSource, _check as check
from dagster._core.launcher import CheckRunHealthResult, LaunchRunContext, ResumeRunContext, RunLauncher, WorkerStatus  # fmt: skip
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster_celery.defaults import task_default_queue
from dagster_celery.launcher import CeleryRunLauncher
from dagster_celery.tags import DAGSTER_CELERY_QUEUE_TAG, DAGSTER_CELERY_TASK_ID_TAG
from dagster_k8s.job import USER_DEFINED_K8S_CONFIG_KEY
from dagster_k8s.launcher import K8sRunLauncher
from typing_extensions import Self, override

if TYPE_CHECKING:
    from dagster._config import UserConfigSchema


DEFAULT_CELERY_TAG_KEY = "run-launcher"
DEFAULT_CELERY_TAG_VALUE = "celery"

DEFAULT_CODE_LOCATION_TAG_KEY = "code-location"
DEFAULT_RELEASE_VERSION_TAG_KEY = "release-version"
DEFAULT_RESOLVED_QUEUE_TAG_KEY = "resolved-celery-queue"

CELERY_BROKER_URL_ENV = "CELERY_BROKER_URL"
CELERY_RESULT_BACKEND_ENV = "CELERY_RESULT_BACKEND"
CELERY_DEFAULT_QUEUE_ENV = "CELERY_DEFAULT_QUEUE"

QUEUE_NAME_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def _normalize_queue_part(value: str) -> str:
    value = value.strip().replace("-", "_")
    value = QUEUE_NAME_PATTERN.sub("_", value)
    return value.strip("_")


def _env_name_for_active_version(code_location: str) -> str:
    normalized = _normalize_queue_part(code_location).upper()
    return f"{normalized}_ACTIVE_VERSION"


class HybridCeleryK8sRunLauncher(RunLauncher, ConfigurableClass):
    """Routes entire Dagster runs to versioned Celery queues or Kubernetes Jobs.

    A run is launched in Celery when its ``celery_tag_key`` tag equals
    ``celery_tag_value``. The Celery queue name is constructed from the code location and
    release version. Runs without the selector tag are launched as Kubernetes Jobs.

    The release version is resolved in this order:

    1. The run's ``release_version_tag_key`` tag.
    2. The ``active_versions`` launcher configuration.
    3. An environment variable named ``<NORMALIZED_CODE_LOCATION>_ACTIVE_VERSION``.

    The resolved version and queue are persisted as run tags. This ensures that termination,
    health checks, debugging, and resume operations continue to address the original Celery
    queue.

    For Kubernetes runs with a partition key, the launcher adds the partition and a stable
    partition hash to the run worker pod annotations. Existing user-defined Kubernetes config
    and annotations are preserved.

    Configure the launcher in ``dagster.yaml`` as follows:

    .. code-block:: yaml

        run_launcher:
          module: dagster_celery_k8s
          class: HybridCeleryK8sRunLauncher
          config:
            k8s:
              service_account_name: dagster
              instance_config_map: dagster-instance
              postgres_password_secret: dagster-postgresql-secret
              dagster_home: /opt/dagster/dagster_home
              job_namespace: dagster
            celery_tag_key: run-launcher
            celery_tag_value: celery
            code_location_tag_key: code-location
            release_version_tag_key: release-version
            resolved_queue_tag_key: resolved-celery-queue
            celery_queue_template: "{code_location}_{version}"

    ``CELERY_BROKER_URL`` and ``CELERY_RESULT_BACKEND`` must be available in the environment
    of each process that loads the Dagster instance. ``CELERY_DEFAULT_QUEUE`` is optional and
    defaults to ``dagster``.

    Example Celery run tags:

    .. code-block:: python

        {
            "run-launcher": "celery",
            "code-location": "dagster_alerting",
            "release-version": "3.73.4",
        }

    These tags resolve to the ``dagster_alerting_3_73_4`` Celery queue.
    """

    def __init__(
        self,
        k8s: Mapping[str, Any],
        celery_tag_key: str = DEFAULT_CELERY_TAG_KEY,
        celery_tag_value: str = DEFAULT_CELERY_TAG_VALUE,
        code_location_tag_key: str = DEFAULT_CODE_LOCATION_TAG_KEY,
        release_version_tag_key: str = DEFAULT_RELEASE_VERSION_TAG_KEY,
        resolved_queue_tag_key: str = DEFAULT_RESOLVED_QUEUE_TAG_KEY,
        active_versions: Mapping[str, str] | None = None,
        celery_queue_template: str = "{code_location}_{version}",
        partition_annotation_key: str = "dagster-partition",
        partition_hash_annotation_key: str = "dagster-partition-hash",
        inst_data: ConfigurableClassData | None = None,
    ) -> None:
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        self.celery_tag_key = check.str_param(celery_tag_key, "celery_tag_key")
        self.celery_tag_value = check.str_param(celery_tag_value, "celery_tag_value")
        self.code_location_tag_key = check.str_param(
            code_location_tag_key,
            "code_location_tag_key",
        )
        self.release_version_tag_key = check.str_param(
            release_version_tag_key,
            "release_version_tag_key",
        )
        self.resolved_queue_tag_key = check.str_param(
            resolved_queue_tag_key,
            "resolved_queue_tag_key",
        )
        self.celery_queue_template = check.str_param(
            celery_queue_template,
            "celery_queue_template",
        )
        self.partition_annotation_key = check.str_param(
            partition_annotation_key,
            "partition_annotation_key",
        )
        self.partition_hash_annotation_key = check.str_param(
            partition_hash_annotation_key,
            "partition_hash_annotation_key",
        )
        self.active_versions = dict(
            check.opt_mapping_param(
                active_versions,
                "active_versions",
                key_type=str,
                value_type=str,
            )
        )

        self._celery_config = self._resolve_celery_config()
        self._k8s_config = dict(check.mapping_param(k8s, "k8s"))

        self._default_celery_launcher = CeleryRunLauncher(**self._celery_config)
        self._celery_launchers_by_queue: dict[str, CeleryRunLauncher] = {}
        self._k8s_launcher = K8sRunLauncher(**self._k8s_config)

        super().__init__()

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    def __getattr__(self, name: str) -> Any:
        """Preserve the K8sRunLauncher interface for Kubernetes-specific integrations."""
        try:
            k8s_launcher = object.__getattribute__(self, "_k8s_launcher")
        except AttributeError as exc:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {name!r}"
            ) from exc

        if hasattr(k8s_launcher, name):
            return getattr(k8s_launcher, name)

        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

    @classmethod
    def config_type(cls) -> "UserConfigSchema":
        return {
            "k8s": Field(
                K8sRunLauncher.config_type(),
                is_required=True,
                description="Configuration for K8sRunLauncher.",
            ),
            "celery_tag_key": Field(
                StringSource,
                is_required=False,
                default_value=DEFAULT_CELERY_TAG_KEY,
            ),
            "celery_tag_value": Field(
                StringSource,
                is_required=False,
                default_value=DEFAULT_CELERY_TAG_VALUE,
            ),
            "code_location_tag_key": Field(
                StringSource,
                is_required=False,
                default_value=DEFAULT_CODE_LOCATION_TAG_KEY,
            ),
            "release_version_tag_key": Field(
                StringSource,
                is_required=False,
                default_value=DEFAULT_RELEASE_VERSION_TAG_KEY,
            ),
            "resolved_queue_tag_key": Field(
                StringSource,
                is_required=False,
                default_value=DEFAULT_RESOLVED_QUEUE_TAG_KEY,
            ),
            "active_versions": Field(
                Permissive(),
                is_required=False,
                default_value={},
                description="Mapping from code location name to its active release version.",
            ),
            "celery_queue_template": Field(
                StringSource,
                is_required=False,
                default_value="{code_location}_{version}",
            ),
            "partition_annotation_key": Field(
                StringSource,
                is_required=False,
                default_value="dagster-partition",
            ),
            "partition_hash_annotation_key": Field(
                StringSource,
                is_required=False,
                default_value="dagster-partition-hash",
            ),
        }

    @classmethod
    def from_config_value(
        cls,
        inst_data: ConfigurableClassData,
        config_value: Mapping[str, Any],
    ) -> Self:
        return cls(inst_data=inst_data, **config_value)

    @override
    def register_instance(self, instance: DagsterInstance) -> None:
        super().register_instance(instance)

        self._default_celery_launcher.register_instance(instance)
        self._k8s_launcher.register_instance(instance)

        for launcher in self._celery_launchers_by_queue.values():
            if not launcher.has_instance:
                launcher.register_instance(instance)

    @override
    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run

        if self._should_launch_in_celery(run):
            code_location = self._resolve_code_location(run)
            version = self._resolve_version(run, code_location)
            queue = self._build_queue_name(
                code_location=code_location,
                version=version,
            )

            celery_run = self._run_with_resolved_celery_metadata(
                run=run,
                version=version,
                queue=queue,
            )
            self._persist_resolved_celery_metadata(celery_run)

            self._instance.report_engine_event(
                message=(
                    "Launching Dagster run directly in Celery without a Kubernetes run worker "
                    f"pod. code_location={code_location}, version={version}, queue={queue}"
                ),
                dagster_run=celery_run,
                cls=self.__class__,
            )

            self._get_celery_launcher_for_queue(queue).launch_run(
                LaunchRunContext(
                    dagster_run=celery_run,
                    workspace=context.workspace,
                )
            )
            return

        k8s_context = self._context_with_partition_annotations(context)

        self._instance.report_engine_event(
            message="Launching Dagster run via K8sRunLauncher.",
            dagster_run=k8s_context.dagster_run,
            cls=self.__class__,
        )
        self._k8s_launcher.launch_run(k8s_context)

    @override
    def terminate(self, run_id: str) -> bool:
        run_id = check.str_param(run_id, "run_id")
        run = self._instance.get_run_by_id(run_id)

        if run is None:
            return False

        if self._is_celery_routed_run(run):
            if not self._has_celery_task_id(run):
                return False

            return self._get_celery_launcher_for_existing_run(run).terminate(run_id)

        return self._k8s_launcher.terminate(run_id)

    @property
    def supports_check_run_worker_health(self) -> bool:
        return True

    @override
    def check_run_worker_health(self, run: DagsterRun) -> CheckRunHealthResult:
        if self._is_celery_routed_run(run):
            if not self._has_celery_task_id(run):
                return CheckRunHealthResult(
                    WorkerStatus.NOT_FOUND,
                    "Celery task has not been submitted for this run.",
                )

            return self._get_celery_launcher_for_existing_run(run).check_run_worker_health(run)

        return self._k8s_launcher.check_run_worker_health(run)

    @override
    def get_run_worker_debug_info(
        self,
        run: DagsterRun,
        include_container_logs: bool | None = True,
    ) -> str | None:
        if self._is_celery_routed_run(run):
            if not self._has_celery_task_id(run):
                return (
                    f"Run {run.run_id} is routed to Celery, but no Celery task ID has been "
                    "persisted. Task submission has not completed or has failed."
                )

            return self._get_celery_launcher_for_existing_run(run).get_run_worker_debug_info(
                run,
                include_container_logs=include_container_logs,
            )

        return self._k8s_launcher.get_run_worker_debug_info(
            run,
            include_container_logs=include_container_logs,
        )

    @property
    def supports_resume_run(self) -> bool:
        return (
            self._default_celery_launcher.supports_resume_run
            and self._k8s_launcher.supports_resume_run
        )

    @override
    def resume_run(self, context: ResumeRunContext) -> None:
        run = context.dagster_run

        if self._is_celery_routed_run(run):
            code_location = self._resolve_code_location(run)
            version = self._resolve_version(run, code_location)
            queue = run.tags.get(self.resolved_queue_tag_key)

            if not queue:
                queue = self._build_queue_name(
                    code_location=code_location,
                    version=version,
                )

            celery_run = self._run_with_resolved_celery_metadata(
                run=run,
                version=version,
                queue=queue,
            )
            self._persist_resolved_celery_metadata(celery_run)

            self._get_celery_launcher_for_queue(queue).resume_run(
                ResumeRunContext(
                    dagster_run=celery_run,
                    workspace=context.workspace,
                    resume_attempt_number=context.resume_attempt_number,
                )
            )
            return

        k8s_context = self._context_with_partition_annotations(
            LaunchRunContext(
                dagster_run=run,
                workspace=context.workspace,
            )
        )

        self._k8s_launcher.resume_run(
            ResumeRunContext(
                dagster_run=k8s_context.dagster_run,
                workspace=context.workspace,
                resume_attempt_number=context.resume_attempt_number,
            )
        )

    @override
    def dispose(self) -> None:
        self._default_celery_launcher.dispose()

        for launcher in self._celery_launchers_by_queue.values():
            launcher.dispose()

        self._k8s_launcher.dispose()

    @override
    def join(self, timeout: int = 30) -> None:
        self._default_celery_launcher.join(timeout)

        for launcher in self._celery_launchers_by_queue.values():
            launcher.join(timeout)

        self._k8s_launcher.join(timeout)

    def _should_launch_in_celery(self, run: DagsterRun) -> bool:
        return run.tags.get(self.celery_tag_key) == self.celery_tag_value

    @staticmethod
    def _resolve_celery_config() -> dict[str, Any]:
        broker = os.getenv(CELERY_BROKER_URL_ENV)
        backend = os.getenv(CELERY_RESULT_BACKEND_ENV)
        default_queue = os.getenv(CELERY_DEFAULT_QUEUE_ENV) or task_default_queue

        missing_environment_variables = []
        if not broker:
            missing_environment_variables.append(CELERY_BROKER_URL_ENV)
        if not backend:
            missing_environment_variables.append(CELERY_RESULT_BACKEND_ENV)

        if missing_environment_variables:
            missing = ", ".join(missing_environment_variables)
            raise ValueError(
                "Celery configuration is incomplete. Provide these environment variables: "
                f"{missing}."
            )

        return {
            "broker": broker,
            "backend": backend,
            "default_queue": default_queue,
        }

    def _is_celery_routed_run(self, run: DagsterRun) -> bool:
        return (
            self._should_launch_in_celery(run)
            or self.resolved_queue_tag_key in run.tags
            or DAGSTER_CELERY_TASK_ID_TAG in run.tags
        )

    @staticmethod
    def _has_celery_task_id(run: DagsterRun) -> bool:
        return bool(run.tags.get(DAGSTER_CELERY_TASK_ID_TAG))

    def _get_celery_launcher_for_existing_run(self, run: DagsterRun) -> CeleryRunLauncher:
        queue = run.tags.get(DAGSTER_CELERY_QUEUE_TAG) or run.tags.get(self.resolved_queue_tag_key)

        if queue:
            return self._get_celery_launcher_for_queue(queue)

        return self._default_celery_launcher

    def _get_celery_launcher_for_queue(self, queue: str) -> CeleryRunLauncher:
        if queue not in self._celery_launchers_by_queue:
            config = {**self._celery_config, "default_queue": queue}
            launcher = CeleryRunLauncher(**config)  # ty: ignore[invalid-argument-type]

            if self.has_instance:
                launcher.register_instance(self._instance)

            self._celery_launchers_by_queue[queue] = launcher

        return self._celery_launchers_by_queue[queue]

    def _resolve_code_location(self, run: DagsterRun) -> str:
        code_location = run.tags.get(self.code_location_tag_key)

        if code_location:
            return code_location

        remote_job_origin = getattr(run, "remote_job_origin", None)
        if remote_job_origin:
            repository_origin = getattr(remote_job_origin, "repository_origin", None)
            code_location_origin = getattr(repository_origin, "code_location_origin", None)
            location_name = getattr(code_location_origin, "location_name", None)

            if location_name:
                return location_name

        raise ValueError(
            f"Run {run.run_id} is marked for Celery execution, but code location is not set. "
            f'Add run tag "{self.code_location_tag_key}=<code_location>".'
        )

    def _resolve_version(self, run: DagsterRun, code_location: str) -> str:
        version_from_run = run.tags.get(self.release_version_tag_key)
        if version_from_run:
            return version_from_run

        version_from_config = self.active_versions.get(code_location)
        if version_from_config:
            return version_from_config

        version_env_name = _env_name_for_active_version(code_location)
        version_from_env = os.getenv(version_env_name)
        if version_from_env:
            return version_from_env

        raise ValueError(
            f'Active version for code location "{code_location}" is not configured. '
            f'Set run tag "{self.release_version_tag_key}", '
            f"or config active_versions.{code_location}, "
            f"or env {version_env_name}."
        )

    def _build_queue_name(self, code_location: str, version: str) -> str:
        return self.celery_queue_template.format(
            code_location=_normalize_queue_part(code_location),
            version=_normalize_queue_part(version),
        )

    def _run_with_resolved_celery_metadata(
        self,
        run: DagsterRun,
        version: str,
        queue: str,
    ) -> DagsterRun:
        return run.with_tags(
            {
                **run.tags,
                self.release_version_tag_key: version,
                self.resolved_queue_tag_key: queue,
                DAGSTER_CELERY_QUEUE_TAG: queue,
            }
        )

    def _persist_resolved_celery_metadata(self, run: DagsterRun) -> None:
        self._instance.add_run_tags(
            run.run_id,
            {
                self.release_version_tag_key: run.tags[self.release_version_tag_key],
                self.resolved_queue_tag_key: run.tags[self.resolved_queue_tag_key],
                DAGSTER_CELERY_QUEUE_TAG: run.tags[DAGSTER_CELERY_QUEUE_TAG],
            },
        )

    def _context_with_partition_annotations(
        self,
        context: LaunchRunContext,
    ) -> LaunchRunContext:
        run = context.dagster_run
        partition_key = self._get_partition_key(run)

        if not partition_key:
            return context

        new_tags = dict(run.tags)
        new_tags[USER_DEFINED_K8S_CONFIG_KEY] = self._merge_partition_annotations(
            existing_config_json=new_tags.get(USER_DEFINED_K8S_CONFIG_KEY),
            partition_key=partition_key,
        )

        return LaunchRunContext(
            dagster_run=run.with_tags(new_tags),
            workspace=context.workspace,
        )

    @staticmethod
    def _get_partition_key(run: DagsterRun) -> str | None:
        return run.tags.get(PARTITION_NAME_TAG) or run.tags.get("partition")

    def _merge_partition_annotations(
        self,
        existing_config_json: str | None,
        partition_key: str,
    ) -> str:
        k8s_config = json.loads(existing_config_json) if existing_config_json else {}

        pod_metadata = k8s_config.setdefault("pod_template_spec_metadata", {})
        annotations = pod_metadata.setdefault("annotations", {})

        annotations[self.partition_annotation_key] = partition_key
        annotations[self.partition_hash_annotation_key] = hashlib.sha1(
            partition_key.encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()

        return json.dumps(
            k8s_config,
            ensure_ascii=False,
            sort_keys=True,
        )