{{- define "dagsterYaml.runCoordinator.queued" }}
{{- $queuedRunCoordinatorConfig := .Values.dagsterDaemon.runCoordinator.config.queuedRunCoordinator }}
module: dagster.core.run_coordinator
class: QueuedRunCoordinator
{{- if not (empty (compact (values $queuedRunCoordinatorConfig))) }}
config:
  {{/* Workaround to prevent 0 from being interpreted as falsey: https://github.com/helm/helm/issues/3164#issuecomment-709537506 */}}
  max_concurrent_runs: {{ if (kindIs "invalid" $queuedRunCoordinatorConfig.maxConcurrentRuns) }}-1{{ else }}{{ $queuedRunCoordinatorConfig.maxConcurrentRuns }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.tagConcurrencyLimits }}
  tag_concurrency_limits: {{ $queuedRunCoordinatorConfig.tagConcurrencyLimits | toYaml | nindent 2 }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.dequeueIntervalSeconds }}
  dequeue_interval_seconds: {{ $queuedRunCoordinatorConfig.dequeueIntervalSeconds }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.dequeueUseThreads }}
  dequeue_use_threads: {{ $queuedRunCoordinatorConfig.dequeueUseThreads }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.dequeueNumWorkers }}
  dequeue_num_workers: {{ $queuedRunCoordinatorConfig.dequeueNumWorkers }}
  {{- end }}

  {{- if $queuedRunCoordinatorConfig.blockOpConcurrencyLimitedRuns }}
  block_op_concurrency_limited_runs:
    enabled: {{ $queuedRunCoordinatorConfig.blockOpConcurrencyLimitedRuns.enabled }}
    op_concurrency_slot_buffer: {{ $queuedRunCoordinatorConfig.blockOpConcurrencyLimitedRuns.opConcurrencySlotBuffer }}
  {{- end }}
{{- end }}
{{- end }}

{{- define "dagsterYaml.runCoordinator.custom" }}
{{- $customRunCoordinatorConfig := .Values.dagsterDaemon.runCoordinator.config.customRunCoordinator }}
module: {{ $customRunCoordinatorConfig.module | quote }}
class: {{ $customRunCoordinatorConfig.class | quote }}
config: {{ $customRunCoordinatorConfig.config | toYaml | nindent 2 }}
{{- end }}
