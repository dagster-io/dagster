{{- define "dagsterYaml.scheduler.daemon" }}
{{- $daemonSchedulerConfig := .Values.scheduler.config.daemonScheduler }}
module: dagster.core.scheduler
class: DagsterDaemonScheduler
{{- if not (empty (compact (values $daemonSchedulerConfig))) }}
config:
  {{- if $daemonSchedulerConfig.maxCatchupRuns }}
  max_catchup_runs: {{ $daemonSchedulerConfig.maxCatchupRuns }}
  {{- end }}
  {{- if $daemonSchedulerConfig.maxTickRetries }}
  max_tick_retries: {{ $daemonSchedulerConfig.maxTickRetries }}
  {{- end }}
{{- end }}
{{- end }}

{{- define "dagsterYaml.scheduler.custom" }}
{{- $customSchedulerConfig := .Values.scheduler.config.customScheduler }}
module: {{ $customSchedulerConfig.module | quote }}
class: {{ $customSchedulerConfig.class | quote }}
config: {{ $customSchedulerConfig.config | toYaml | nindent 2 }}
{{- end }}