{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "dagster.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "dagster.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

# Dagit image e.g. repo/foo:bar
{{- define "dagster.dagit_image" -}}
{{ required "Dagit image repository .Values.dagit.image.repository is required" .Values.dagit.image.repository -}}
:
{{- required "Dagit image tag .Values.dagit.image.tag is required" .Values.dagit.image.tag }}
{{- end -}}

# Dagster Run Launcher
{{- define "dagster.validate_one_run_launcher_enabled" -}}
{{- if or (and .Values.celery.enabled .Values.k8sRunLauncher.enabled) (not (or .Values.celery.enabled .Values.k8sRunLauncher.enabled)) -}}
{{- fail "One of `celery.enabled` and `k8sRunLauncher.enabled` should be true." -}}
{{- end -}}
{{- end -}}

{{- define "dagster.celery_k8s_run_launcher_enabled" -}}
{{- include "dagster.validate_one_run_launcher_enabled" . -}}
{{- required "CeleryK8sRunLauncher .Values.celery.enabled is required" .Values.celery.enabled -}}
{{- end -}}

{{- define "dagster.k8s_run_launcher_enabled" -}}
{{- include "dagster.validate_one_run_launcher_enabled" . -}}
{{- required "K8sRunLauncher .Values.k8sRunLauncher.enabled is required" .Values.k8sRunLauncher.enabled -}}
{{- end -}}

# Dagster Celery worker image e.g. repo/foo:bar
{{- define "dagster.celery_image" -}}
{{ required "Celery worker image repository .Values.celery.image.repository is required" .Values.celery.image.repository -}}
:
{{- required "Celery worker image tag .Values.celery.image.tag is required" .Values.celery.image.tag }}
{{- end -}}

{{- define "dagster.dagit.scheduleUpCommand" -}}
{{- if .Values.userDeployments.enabled }}
{{- range $deployment := .Values.userDeployments.deployments }}
/usr/local/bin/dagster schedule up -w /dagster-workspace/workspace.yaml --location {{$deployment.name}};
{{- end -}}
dagit -h 0.0.0.0 -p 80 -w /dagster-workspace/workspace.yaml
{{- end -}}
{{- end -}}

{{- define "dagster.dagit.fullname" -}}
{{- $name := default "dagit" .Values.dagit.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.workers.fullname" -}}
{{- $name := default "celery-workers" .Values.celery.workers.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.flower.fullname" -}}
{{- $name := default "flower" .Values.flower.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.rabbitmq.fullname" -}}
{{- $name := default "rabbitmq" .Values.rabbitmq.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified postgresql name or use the `postgresqlHost` value if defined.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "dagster.postgresql.fullname" -}}
{{- if .Values.postgresql.postgresqlHost }}
    {{- .Values.postgresql.postgresqlHost -}}
{{- else }}
    {{- $name := default "postgresql" .Values.postgresql.nameOverride -}}
    {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "dagster.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "dagster.labels" -}}
helm.sh/chart: {{ include "dagster.chart" . }}
{{ include "dagster.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "dagster.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dagster.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "dagster.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default (include "dagster.fullname" .) .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Set postgres host
See: https://github.com/helm/charts/blob/61c2cc0db49b06b948f90c8e44e9143d7bab430d/stable/sentry/templates/_helpers.tpl#L59-L68
*/}}
{{- define "dagster.postgresql.host" -}}
{{- if .Values.postgresql.enabled -}}
{{- template "dagster.postgresql.fullname" . -}}
{{- else -}}
{{- .Values.postgresql.postgresqlHost | quote -}}
{{- end -}}
{{- end -}}

{{/*
Celery options
*/}}
{{- define "dagster.celery.broker_url" -}}
{{- if .Values.rabbitmq.enabled -}}
pyamqp://{{ .Values.rabbitmq.rabbitmq.username }}:{{ .Values.rabbitmq.rabbitmq.password }}@{{ include "dagster.rabbitmq.fullname" . }}:{{ .Values.rabbitmq.service.port }}//
{{- else if .Values.redis.enabled -}}
redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/{{ .Values.redis.brokerDbNumber | default 0}}
{{- end -}}
{{- end -}}

{{- define "dagster.celery.backend_url" -}}
{{- if .Values.rabbitmq.enabled -}}
rpc://
{{- else if .Values.redis.enabled -}}
redis://{{ .Values.redis.host }}:{{ .Values.redis.port }}/{{ .Values.redis.backendDbNumber | default 0}}
{{- end -}}
{{- end -}}

{{/*
This environment shared across all containers.

This includes Dagit, Celery Workers, Run Master, and Step Execution containers.
*/}}
{{- define "dagster.shared_env" -}}
DAGSTER_HOME: "{{ .Values.dagster_home }}"
DAGSTER_K8S_CELERY_BROKER: "{{ template "dagster.celery.broker_url" . }}"
DAGSTER_K8S_CELERY_BACKEND: "{{ template "dagster.celery.backend_url" . }}"
DAGSTER_K8S_PG_PASSWORD_SECRET: "{{ template "dagster.fullname" .}}-postgresql-secret"
DAGSTER_K8S_INSTANCE_CONFIG_MAP: "{{ template "dagster.fullname" .}}-instance"
DAGSTER_K8S_PIPELINE_RUN_NAMESPACE: "{{ .Release.Namespace }}"
DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP: "{{ template "dagster.fullname" . }}-pipeline-env"
DAGSTER_K8S_PIPELINE_RUN_IMAGE: "{{- .Values.pipeline_run.image.repository -}}:{{- .Values.pipeline_run.image.tag -}}"
DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY: "{{ .Values.pipeline_run.image.pullPolicy }}"
{{- end -}}