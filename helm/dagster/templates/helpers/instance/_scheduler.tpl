{{- define "dagsterYaml.scheduler.daemon" }}
module: dagster.core.scheduler
class: DagsterDaemonScheduler
{{- end }}

{{- define "dagsterYaml.scheduler.custom" }}
{{- $customSchedulerConfig := .Values.scheduler.config.customScheduler }}
module: {{ $customSchedulerConfig.module | quote }}
class: {{ $customSchedulerConfig.class | quote }}
config: {{ $customSchedulerConfig.config | toYaml | nindent 2 }}
{{- end }}