{{- define "dagsterYaml.postgresql.config" }}
postgres_db:
  username: {{ .Values.postgresql.postgresqlUsername }}
  password:
    env: DAGSTER_PG_PASSWORD
  hostname: {{ include "dagster.postgresql.host" . }}
  db_name: {{ .Values.postgresql.postgresqlDatabase	}}
  port: {{ .Values.postgresql.service.port }}
  params: {{- .Values.postgresql.postgresqlParams | toYaml | nindent 4 }}
  {{- if .Values.postgresql.postgresqlScheme }}
  scheme: {{ .Values.postgresql.postgresqlScheme }}
  {{- end }}
{{- end }}
