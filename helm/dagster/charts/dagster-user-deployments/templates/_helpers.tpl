{{/*
Handle deployments - detect if array or map and output ready for range loop in calling template.
For map format, inject the key as the "name" field into each deployment object.
*/}}
{{- define "dagster-user-deployments.deployments" -}}
{{- if kindIs "map" .Values.deployments -}}
{{- /* Dictionary format: range over map */ -}}
{{ range $name, $deployment := .Values.deployments -}}
{{ $deployment | merge (dict "name" $name) | toJson }}
{{ end -}}
{{- else -}}
{{- /* Array format: range over array */ -}}
{{ range $deployment := .Values.deployments -}}
{{ $deployment | toJson }}
{{ end -}}
{{- end -}}
{{- end }}




