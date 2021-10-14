{{- define "stringSource" }}
{{- $tp := typeOf . }}

{{- if eq $tp "map[string]interface {}" }}
  {{- . | toYaml | nindent 4 }}
{{- else if eq $tp "string" }}
  {{- . | quote }}
{{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.noop" }}
module: dagster.core.storage.noop_compute_log_manager
class: NoOpComputeLogManager
{{- end }}

{{- define "dagsterYaml.computeLogManager.azure" }}
{{- $azureBlobComputeLogManagerConfig := .Values.computeLogManager.config.azureBlobComputeLogManager }}
module: dagster_azure.blob.compute_log_manager
class: AzureBlobComputeLogManager
config:
  storage_account: {{ include "stringSource" $azureBlobComputeLogManagerConfig.storageAccount }}
  container: {{ include "stringSource" $azureBlobComputeLogManagerConfig.container }}
  secret_key: {{ include "stringSource" $azureBlobComputeLogManagerConfig.secretKey }}

  {{- if $azureBlobComputeLogManagerConfig.localDir }}
  local_dir: {{ include "stringSource" $azureBlobComputeLogManagerConfig.localDir }}
  {{- end }}

  {{- if $azureBlobComputeLogManagerConfig.prefix }}
  prefix: {{ include "stringSource" $azureBlobComputeLogManagerConfig.prefix }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.gcs" }}
{{- $gcsComputeLogManagerConfig := .Values.computeLogManager.config.gcsComputeLogManager }}
module: dagster_gcp.gcs.compute_log_manager
class: GCSComputeLogManager
config:
  bucket: {{ include "stringSource" $gcsComputeLogManagerConfig.bucket }}

  {{- if $gcsComputeLogManagerConfig.localDir }}
  local_dir: {{ include "stringSource" $gcsComputeLogManagerConfig.localDir }}
  {{- end }}

  {{- if $gcsComputeLogManagerConfig.prefix }}
  prefix: {{ include "stringSource" $gcsComputeLogManagerConfig.prefix }}
  {{- end }}

  {{- if $gcsComputeLogManagerConfig.jsonCredentialsEnvvar }}
  json_credentials_envvar: {{ include "stringSource" $gcsComputeLogManagerConfig.jsonCredentialsEnvvar }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.s3" }}
{{- $s3ComputeLogManagerConfig := .Values.computeLogManager.config.s3ComputeLogManager }}
module: dagster_aws.s3.compute_log_manager
class: S3ComputeLogManager
config:
  bucket: {{ include "stringSource" $s3ComputeLogManagerConfig.bucket }}

  {{- if $s3ComputeLogManagerConfig.localDir }}
  local_dir: {{ include "stringSource" $s3ComputeLogManagerConfig.localDir }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.prefix }}
  prefix: {{ include "stringSource" $s3ComputeLogManagerConfig.prefix }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.useSsl }}
  use_ssl: {{ $s3ComputeLogManagerConfig.useSsl }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.verify }}
  verify: {{ $s3ComputeLogManagerConfig.verify }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.verifyCertPath }}
  verify_cert_path: {{ include "stringSource" $s3ComputeLogManagerConfig.verifyCertPath }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.endpointUrl }}
  endpoint_url: {{ include "stringSource" $s3ComputeLogManagerConfig.endpointUrl }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.skipEmptyFiles }}
  skip_empty_files: {{ $s3ComputeLogManagerConfig.skipEmptyFiles }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.custom" }}
{{- $customComputeLogManagerConfig := .Values.computeLogManager.config.customComputeLogManager }}
module: {{ $customComputeLogManagerConfig.module | quote }}
class: {{ $customComputeLogManagerConfig.class | quote }}
config: {{ $customComputeLogManagerConfig.config | toYaml | nindent 2 }}
{{- end }}
