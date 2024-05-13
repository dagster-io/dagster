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
{{- if .Values.global.fullnameOverride -}}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.global.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

# Image utils
{{- define "dagster.externalImage.name" }}
{{- .repository -}}:{{- .tag -}}
{{- end }}

{{- define "dagster.dagsterImage.name" }}
  {{- $ := index . 0 }}

  {{- with index . 1 }}
    {{- /* Filter the tag to parse strings, string integers, and string floats. */}}
    {{- $tag := .tag | default $.Chart.Version | toYaml | trimAll "\"" }}
    {{- printf "%s:%s" .repository $tag }}
  {{- end }}
{{- end }}

{{- define "dagster.webserver.dagsterWebserverCommand" -}}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}
{{- $userDeployments := index .Values "dagster-user-deployments" }}
{{- printf "dagster-webserver -h 0.0.0.0 -p"}} {{ $_.Values.dagsterWebserver.service.port }}
{{- if $userDeployments.enabled }} -w /dagster-workspace/workspace.yaml {{- end -}}
{{- with $_.Values.dagsterWebserver.dbStatementTimeout }} --db-statement-timeout {{ . }} {{- end -}}
{{- with $_.Values.dagsterWebserver.dbPoolRecycle }} --db-pool-recycle {{ . }} {{- end -}}
{{- if $_.Values.dagsterWebserver.pathPrefix }} --path-prefix {{ $_.Values.dagsterWebserver.pathPrefix }} {{- end -}}
{{- with $_.Values.dagsterWebserver.logLevel }} --log-level {{ . }} {{- end -}}
{{- if .webserverReadOnly }} --read-only {{- end -}}
{{- end -}}

{{- define "dagster.dagsterDaemon.daemonCommand" -}}
{{- $userDeployments := index .Values "dagster-user-deployments" -}}
dagster-daemon run
{{- if $userDeployments.enabled }} -w /dagster-workspace/workspace.yaml {{- end -}}
{{- end -}}

{{- define "dagster.webserver.fullname" -}}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}
{{- $name := default "webserver" $_.Values.dagsterWebserver.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- if .webserverReadOnly -}} -read-only {{- end -}}
{{- end -}}

{{- define "dagster.webserver.componentName" -}}
dagster-webserver {{- if .webserverReadOnly -}} -read-only {{- end -}}
{{- end -}}

{{- define "dagster.webserver.migrate" -}}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}
{{- $name := default "dagster-webserver" $_.Values.dagsterWebserver.nameOverride -}}
{{- printf "%s-%s-instance-migrate" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "dagster.workers.fullname" -}}
{{- $celeryK8sRunLauncherConfig := .Values.runLauncher.config.celeryK8sRunLauncher }}
{{- $name := $celeryK8sRunLauncherConfig.nameOverride -}}
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

{{- define "dagster.postgresql.pgisready" -}}
until pg_isready -h {{ include "dagster.postgresql.host" . }} -p {{ .Values.postgresql.service.port }} -U {{ .Values.postgresql.postgresqlUsername }}; do echo waiting for database; sleep 2; done;
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
{{- .Values.global.serviceAccountName | default .Values.serviceAccount.name | default (include "dagster.fullname" .) }}
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

{{- define "dagster.postgresql.secretName" -}}
{{- if .Values.global.postgresqlSecretName }}
{{- .Values.global.postgresqlSecretName }}
{{- else }}
{{- printf "%s-postgresql-secret" (include "dagster.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Celery options
*/}}
{{- define "dagster.celery.broker_url" -}}
{{- if .Values.rabbitmq.enabled -}}
pyamqp://{{ .Values.rabbitmq.rabbitmq.username }}:{{ .Values.rabbitmq.rabbitmq.password }}@{{ include "dagster.rabbitmq.fullname" . }}:{{ .Values.rabbitmq.service.port }}//
{{- else if .Values.redis.enabled -}}
{{- $password := ternary (printf ":%s@" .Values.redis.password) "" .Values.redis.usePassword -}}
{{- $connectionUrl := printf "redis://%s%s:%g/%g" $password .Values.redis.host .Values.redis.port (.Values.redis.brokerDbNumber | default (float64 0)) -}}
{{- ternary .Values.redis.brokerUrl $connectionUrl (not (empty .Values.redis.brokerUrl)) }}
{{- end -}}
{{- end -}}

{{- define "dagster.celery.backend_url" -}}
{{- if .Values.rabbitmq.enabled -}}
rpc://
{{- else if .Values.redis.enabled -}}
{{- $password := ternary (printf ":%s@" .Values.redis.password) "" .Values.redis.usePassword -}}
{{- $connectionUrl := printf "redis://%s%s:%g/%g" $password .Values.redis.host .Values.redis.port (.Values.redis.backendDbNumber | default (float64 0)) -}}
{{- ternary .Values.redis.backendUrl $connectionUrl (not (empty .Values.redis.backendUrl)) }}
{{- end -}}
{{- end -}}

{{- define "dagster.rabbitmq.alivenessTest" -}}
until wget http://{{ .Values.rabbitmq.rabbitmq.username }}:{{ .Values.rabbitmq.rabbitmq.password }}@{{ include "dagster.rabbitmq.fullname" . }}:{{ .Values.rabbitmq.service.managerPort }}/api/aliveness-test/%2F; do echo waiting for rabbitmq; sleep 2; done;
{{- end -}}

{{/*
This environment shared across all containers.

This includes the Dagster webserver, Celery Workers, Run Worker, and Step Worker containers.
*/}}
{{- define "dagster.shared_env" -}}
DAGSTER_HOME: {{ .Values.global.dagsterHome | quote }}
DAGSTER_K8S_PIPELINE_RUN_NAMESPACE: "{{ .Release.Namespace }}"
DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP: "{{ template "dagster.fullname" . }}-pipeline-env"
DAGSTER_K8S_PIPELINE_RUN_IMAGE: {{ include "dagster.dagsterImage.name" (list $ .Values.pipelineRun.image) | quote }}
DAGSTER_K8S_PIPELINE_RUN_IMAGE_PULL_POLICY: "{{ .Values.pipelineRun.image.pullPolicy }}"
{{- end -}}

{{/* Assigns an ingress path port to the correct key based on its type */}}
{{- define "ingress.service.port" -}}
  {{- $portType := typeOf .servicePort }}
  {{- if eq $portType "string" }}
  name: {{ .servicePort }}
  {{- else }}
  number: {{ .servicePort }}
  {{- end }}
{{- end }}

{{- define "dagster.workspace.configmapName" -}}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}
{{- $webserverWorkspace := $_.Values.dagsterWebserver.workspace }}
{{- if and $webserverWorkspace.enabled $webserverWorkspace.externalConfigmap }}
{{- $webserverWorkspace.externalConfigmap -}}
{{- else -}}
{{ template "dagster.fullname" . }}-workspace-yaml
{{- end -}}
{{- end -}}
