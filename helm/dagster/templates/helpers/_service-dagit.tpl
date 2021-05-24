{{ define "service-dagit" }}

apiVersion: v1
kind: Service
metadata:
  name: {{ include "dagster.dagit.fullname" . }}
  labels:
    {{- include "dagster.labels" . | nindent 4 }}
    component: {{ include "dagster.dagit.componentName" . }}
  annotations:
    {{- range $key, $value := .Values.dagit.service.annotations }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
spec:
  type: {{ .Values.dagit.service.type | default "ClusterIP" }}
  ports:
    - port: {{ .Values.dagit.service.port | default 80 }}
      protocol: TCP
      name: http
  selector:
    {{- include "dagster.selectorLabels" . | nindent 4 }}
    component: {{ include "dagster.dagit.componentName" . }}

{{ end }}
