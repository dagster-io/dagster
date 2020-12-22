{{- define "dagsterYaml.computeLogManager.azure" }}
{{- $azureBlobComputeLogManagerConfig := .Values.computeLogManager.config.azureBlobComputeLogManager }}
module: dagster_azure.blob.compute_log_manager
class: AzureBlobComputeLogManager
config:
  storage_account: {{ $azureBlobComputeLogManagerConfig.storageAccount | quote }}
  container: {{ $azureBlobComputeLogManagerConfig.container | quote }}
  secret_key: {{ $azureBlobComputeLogManagerConfig.secretKey | quote }}

  {{- if $azureBlobComputeLogManagerConfig.localDir }}
  local_dir: {{ $azureBlobComputeLogManagerConfig.localDir | quote }}
  {{- end }}

  {{- if $azureBlobComputeLogManagerConfig.prefix }}
  prefix: {{ $azureBlobComputeLogManagerConfig.prefix | quote }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.gcs" }}
{{- $gcsComputeLogManagerConfig := .Values.computeLogManager.config.gcsComputeLogManager }}
module: dagster_gcp.gcs.compute_log_manager
class: GCSComputeLogManager
config:
  bucket: {{ $gcsComputeLogManagerConfig.bucket | quote }}

  {{- if $gcsComputeLogManagerConfig.localDir }}
  local_dir: {{ $gcsComputeLogManagerConfig.localDir | quote }}
  {{- end }}

  {{- if $gcsComputeLogManagerConfig.prefix }}
  prefix: {{ $gcsComputeLogManagerConfig.prefix | quote }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.s3" }}
{{- $s3ComputeLogManagerConfig := .Values.computeLogManager.config.s3ComputeLogManager }}
module: dagster_aws.s3.compute_log_manager
class: S3ComputeLogManager
config:
  bucket: {{ $s3ComputeLogManagerConfig.bucket | quote }}

  {{- if $s3ComputeLogManagerConfig.localDir }}
  local_dir: {{ $s3ComputeLogManagerConfig.localDir | quote }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.prefix }}
  prefix: {{ $s3ComputeLogManagerConfig.prefix | quote }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.useSsl }}
  use_ssl: {{ $s3ComputeLogManagerConfig.useSsl }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.verify }}
  verify: {{ $s3ComputeLogManagerConfig.verify }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.verifyCertPath }}
  verify_cert_path: {{ $s3ComputeLogManagerConfig.verifyCertPath | quote }}
  {{- end }}

  {{- if $s3ComputeLogManagerConfig.endpointUrl }}
  endpoint_url: {{ $s3ComputeLogManagerConfig.endpointUrl | quote }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.computeLogManager.custom" }}
{{- $customComputeLogManagerConfig := .Values.computeLogManager.config.customComputeLogManager }}
module: {{ $customComputeLogManagerConfig.module | quote }}
class: {{ $customComputeLogManagerConfig.class | quote }}
config: {{ toYaml $customComputeLogManagerConfig.config | nindent 2 }}
{{- end }}
