{{- define "dagsterYaml.runCoordinator.queued" }}
{{- $queuedRunCoordinatorConfig := .Values.dagsterDaemon.runCoordinator.config.queuedRunCoordinator }}
{{- $concurrencyEnabled := .Values.concurrency.enabled }}
module: dagster.core.run_coordinator
class: QueuedRunCoordinator
{{- if not (empty (compact (values $queuedRunCoordinatorConfig))) }}
config:
  {{/* Workaround to prevent 0 from being interpreted as falsey: https://github.com/helm/helm/issues/3164#issuecomment-709537506 */}}
  {{/* Only set max_concurrent_runs if concurrency disabled OR explicitly set */}}
  {{- if or (not $concurrencyEnabled) (not (kindIs "invalid" $queuedRunCoordinatorConfig.maxConcurrentRuns)) }}
  max_concurrent_runs: {{ if (kindIs "invalid" $queuedRunCoordinatorConfig.maxConcurrentRuns) }}-1{{ else }}{{ $queuedRunCoordinatorConfig.maxConcurrentRuns }}
  {{- end }}
  {{- end }}

  {{/* Only set tag_concurrency_limits if concurrency disabled OR explicitly set */}}
  {{- if and $queuedRunCoordinatorConfig.tagConcurrencyLimits (or (not $concurrencyEnabled) (gt (len $queuedRunCoordinatorConfig.tagConcurrencyLimits) 0)) }}
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

  {{/* Only set block_op_concurrency_limited_runs if concurrency disabled OR explicitly set */}}
  {{- if and $queuedRunCoordinatorConfig.blockOpConcurrencyLimitedRuns (or (not $concurrencyEnabled) $queuedRunCoordinatorConfig.blockOpConcurrencyLimitedRuns) }}
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
