{{- define "dagsterYaml.concurrency" }}
{{- $concurrencyConfig := .Values.concurrency }}
{{- $pools := $concurrencyConfig.pools }}
{{- $runs := $concurrencyConfig.runs }}

{{- /* Validate no conflicts with run_coordinator config */ -}}
{{- if and .Values.dagsterDaemon.runCoordinator.enabled (eq .Values.dagsterDaemon.runCoordinator.type "QueuedRunCoordinator") }}
  {{- $qrc := .Values.dagsterDaemon.runCoordinator.config.queuedRunCoordinator }}
  {{- if and (not (kindIs "invalid" $runs.maxConcurrentRuns)) (not (kindIs "invalid" $qrc.maxConcurrentRuns)) }}
    {{- fail "Cannot set both concurrency.runs.maxConcurrentRuns and dagsterDaemon.runCoordinator.config.queuedRunCoordinator.maxConcurrentRuns" }}
  {{- end }}
  {{- if and (gt (len $runs.tagConcurrencyLimits) 0) (gt (len $qrc.tagConcurrencyLimits) 0) }}
    {{- fail "Cannot set both concurrency.runs.tagConcurrencyLimits and dagsterDaemon.runCoordinator.config.queuedRunCoordinator.tagConcurrencyLimits" }}
  {{- end }}
  {{- if and (not (kindIs "invalid" $pools.opGranularityRunBuffer)) $qrc.blockOpConcurrencyLimitedRuns }}
    {{- if not (kindIs "invalid" $qrc.blockOpConcurrencyLimitedRuns.opConcurrencySlotBuffer) }}
      {{- fail "Cannot set both concurrency.pools.opGranularityRunBuffer and dagsterDaemon.runCoordinator.config.queuedRunCoordinator.blockOpConcurrencyLimitedRuns.opConcurrencySlotBuffer" }}
    {{- end }}
  {{- end }}
{{- end }}

{{- /* Render pools config */ -}}
{{- if or (not (kindIs "invalid" $pools.defaultLimit)) $pools.granularity (not (kindIs "invalid" $pools.opGranularityRunBuffer)) }}
pools:
  {{- if not (kindIs "invalid" $pools.defaultLimit) }}
  default_limit: {{ $pools.defaultLimit }}
  {{- end }}
  {{- if $pools.granularity }}
  granularity: {{ $pools.granularity }}
  {{- end }}
  {{- if not (kindIs "invalid" $pools.opGranularityRunBuffer) }}
  op_granularity_run_buffer: {{ $pools.opGranularityRunBuffer }}
  {{- end }}
{{- end }}

{{- /* Render runs config */ -}}
{{- if or (not (kindIs "invalid" $runs.maxConcurrentRuns)) (gt (len $runs.tagConcurrencyLimits) 0) }}
runs:
  {{- if not (kindIs "invalid" $runs.maxConcurrentRuns) }}
  max_concurrent_runs: {{ $runs.maxConcurrentRuns }}
  {{- end }}
  {{- if gt (len $runs.tagConcurrencyLimits) 0 }}
  tag_concurrency_limits:
    {{- range $runs.tagConcurrencyLimits }}
    - key: {{ .key | quote }}
      {{- if .value }}
      value: {{ .value | toYaml | nindent 8 }}
      {{- end }}
      limit: {{ .limit }}
    {{- end }}
  {{- end }}
{{- end }}
{{- end }}
