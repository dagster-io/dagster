{{/*
Return the proper image name

```
{{ include "common.images.image" ( dict "imageRoot" .Values.path.to.the.image) }}
```

Example:

```
# Define the following image in values.yaml
image:
  registry: docker.io
  repository: bitnami/postgresql
  tag: 11.6.0-debian-9-r0
```

```
# Use in the template
{{ include "common.images.image" ( dict "imageRoot" .Values.image ) }}
```

*/}}
{{- define "common.images.image" -}}
{{- $registryName := ( default .imageRoot.registry "docker.io" ) -}}
{{- $repositoryName := .imageRoot.repository -}}
{{- $separator := ":" -}}
{{- $termination := .imageRoot.tag | toString -}}
{{- if .imageRoot.digest -}}
    {{- $separator = "@" -}}
    {{- $termination = .imageRoot.digest | toString -}}
{{- end -}}
{{- printf "%s/%s%s%s" $registryName $repositoryName $separator $termination -}}
{{- end -}}
