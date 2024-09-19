{{ define "service-webserver" }}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}

apiVersion: v1
kind: Service
metadata:
  name: {{ include "dagster.webserver.fullname" . }}
  labels:
    {{- include "dagster.labels" . | nindent 4 }}
    component: {{ include "dagster.webserver.componentName" . }}
  annotations:
    {{- range $key, $value := $_.Values.dagsterWebserver.service.annotations }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
spec:
  type: {{ $_.Values.dagsterWebserver.service.type | default "ClusterIP" }}
  ports:
    - port: {{ $_.Values.dagsterWebserver.service.port | default 80 }}
      protocol: TCP
      name: http
  selector:
    {{- include "dagster.selectorLabels" . | nindent 4 }}
    component: {{ include "dagster.webserver.componentName" . }}

{{ end }}
