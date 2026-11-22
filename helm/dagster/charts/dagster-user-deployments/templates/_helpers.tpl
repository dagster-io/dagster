{{/*
Handle deployments - detect if array or map and output ready for range loop in calling template.
For map format, inject the key as the "name" field into each deployment object. Map keys
are sorted before ranging so the rendered manifest order is stable across `helm template`
runs (Go map iteration order is randomized, which would otherwise produce spurious diffs
for GitOps tooling comparing rendered output).
*/}}
{{- define "dagster-user-deployments.deployments" -}}
{{- if kindIs "map" .Values.deployments -}}
{{- /* Dictionary format: range over map keys in sorted order for stable output */ -}}
{{- range $name := keys .Values.deployments | sortAlpha -}}
{{ index $.Values.deployments $name | merge (dict "name" $name) | toJson }}
{{ end -}}
{{- else -}}
{{- /* Array format: range over array */ -}}
{{ range $deployment := .Values.deployments -}}
{{ $deployment | toJson }}
{{ end -}}
{{- end -}}
{{- end }}
