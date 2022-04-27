{{- define "dagsterYaml.runCoordinator.queued" }}
{{- $queuedRunCoordinatorConfig := .Values.dagsterDaemon.runCoordinator.config.queuedRunCoordinator }}
module: dagster.core.run_coordinator
class: QueuedRunCoordinator
{{- if not (empty (compact (values $queuedRunCoordinatorConfig))) }}
config:
  # Workaround to prevent 0 from being interpreted as falsey:
  # https://github.com/helm/helm/issues/3164#issuecomment-709537506
  {{- if not (kindIs "invalid" $queuedRunCoordinatorConfig.maxConcurrentRuns) }}
  max_concurrent_runs: {{ $queuedRunCoordinatorConfig.maxConcurrentRuns }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.tagConcurrencyLimits }}
  tag_concurrency_limits: {{ $queuedRunCoordinatorConfig.tagConcurrencyLimits | toYaml | nindent 2 }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.dequeueIntervalSeconds }}
  dequeue_interval_seconds: {{ $queuedRunCoordinatorConfig.dequeueIntervalSeconds }}
  {{- end }}
{{- end }}
{{- end }}

{{- define "dagsterYaml.runCoordinator.custom" }}
{{- $customRunCoordinatorConfig := .Values.dagsterDaemon.runCoordinator.config.customRunCoordinator }}
module: {{ $customRunCoordinatorConfig.module | quote }}
class: {{ $customRunCoordinatorConfig.class | quote }}
config: {{ $customRunCoordinatorConfig.config | toYaml | nindent 2 }}
{{- end }}
