{{/*
Renders a Gateway API HTTPRoute for a single service. Besides the usual chart context, expects:

- name: name of the HTTPRoute
- route: route configuration, e.g. `.Values.httpRoute.dagsterWebserver`
- routeKey: key of the route configuration in `.Values.httpRoute`, used in error messages
- serviceName: name of the service to route to
- servicePort: port of the service to route to
*/}}
{{ define "httproute" }}
{{- $parentRefs := .route.parentRefs | default .Values.httpRoute.parentRefs }}
{{- if not $parentRefs }}
{{ fail (printf "httpRoute.parentRefs or httpRoute.%s.parentRefs must be set if httpRoute is enabled." .routeKey) }}
{{- end }}
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: {{ .name }}
  labels:
    {{- include "dagster.labels" . | nindent 4 }}
    {{- range $key, $value := .Values.httpRoute.labels }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
  annotations:
    {{- range $key, $value := .Values.httpRoute.annotations }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
spec:
  parentRefs:
    {{- toYaml $parentRefs | nindent 4 }}
  {{- with .route.hostnames }}
  hostnames:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  rules:
    - matches:
        - path:
            type: {{ .route.pathType }}
            value: {{ .route.path | default "/" | quote }}
      {{- with .route.filters }}
      filters:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      backendRefs:
        - name: {{ .serviceName }}
          port: {{ .servicePort }}
      {{- with .route.timeouts }}
      timeouts:
        {{- toYaml . | nindent 8 }}
      {{- end }}
    {{- with .route.additionalRules }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
{{ end }}
