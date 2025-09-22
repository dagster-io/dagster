{{- define "dagsterYaml.defsStateStorage.blobStorage" }}
{{- $blobStorageConfig := .Values.defsStateStorage.config.blobStorageStateStorage }}
module: dagster._core.storage.defs_state.blob_storage_state_storage
class: BlobStorageStateStorage
config:
  base_path: {{ $blobStorageConfig.basePath | quote }}
  {{- if $blobStorageConfig.storageOptions }}
  storage_options: {{- $blobStorageConfig.storageOptions | toYaml | nindent 4 }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.defsStateStorage.custom" }}
{{- $customConfig := .Values.defsStateStorage.config.customDefsStateStorage }}
module: {{ $customConfig.module | quote }}
class: {{ $customConfig.class | quote }}
{{- if $customConfig.config }}
config:
  {{- $customConfig.config | toYaml | nindent 2 }}
{{- end }}
{{- end }}
