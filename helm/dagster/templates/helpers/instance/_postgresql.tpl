{{- define "dagsterYaml.postgresql.config" }}
postgres_db:
  username: {{ .Values.postgresql.postgresqlUsername }}
  {{- if not .Values.global.postgresqlAuthWifEnabled }}
  password:
    env: DAGSTER_PG_PASSWORD
  {{- end }}
  hostname: {{ include "dagster.postgresql.host" . }}
  db_name: {{ .Values.postgresql.postgresqlDatabase	}}
  port: {{ .Values.postgresql.service.port }}
  params: {{- .Values.postgresql.postgresqlParams | toYaml | nindent 4 }}
  {{- if .Values.postgresql.postgresqlScheme }}
  scheme: {{ .Values.postgresql.postgresqlScheme }}
  {{- end }}
{{- if .Values.global.postgresqlAuthWifEnabled }}
{{- if not (or (eq .Values.postgresql.authProvider.type "azure_wif") (eq .Values.postgresql.authProvider.type "gcp_wif") (eq .Values.postgresql.authProvider.type "aws_wif")) }}
{{- fail (printf "postgresql.authProvider.type must be one of azure_wif, gcp_wif, aws_wif when postgresqlAuthWifEnabled is true; got %q" .Values.postgresql.authProvider.type) }}
{{- end }}
auth_provider:
  {{- if eq .Values.postgresql.authProvider.type "azure_wif" }}
  azure_wif:
    scope: {{ .Values.postgresql.authProvider.azureScope | quote }}
  {{- else if eq .Values.postgresql.authProvider.type "gcp_wif" }}
  gcp_wif: {}
  {{- else if eq .Values.postgresql.authProvider.type "aws_wif" }}
  {{- if not .Values.postgresql.authProvider.awsRegion }}
  {{- fail "postgresql.authProvider.awsRegion is required when type is aws_wif" }}
  {{- end }}
  aws_wif:
    region: {{ .Values.postgresql.authProvider.awsRegion | quote }}
  {{- end }}
{{- end }}
{{- end }}
