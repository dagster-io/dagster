{{ define "deployment-dagit" }}
{{- $userDeployments := index .Values "dagster-user-deployments" }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ template "dagster.dagit.fullname" . }}
  labels:
    {{- include "dagster.labels" . | nindent 4 }}
    component: {{ include "dagster.dagit.componentName" . }}
    {{- with .Values.dagit.deploymentLabels }}
    {{- . | toYaml | nindent 4 }}
    {{- end }}
  annotations:
    {{- range $key, $value := .Values.dagit.annotations }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
spec:
  replicas: {{ .Values.dagit.replicaCount }}
  selector:
    matchLabels:
      {{- include "dagster.selectorLabels" . | nindent 6 }}
      component: {{ include "dagster.dagit.componentName" . }}
  template:
    metadata:
      labels:
        {{- include "dagster.selectorLabels" . | nindent 8 }}
        component: {{ include "dagster.dagit.componentName" . }}
        {{- with .Values.dagit.labels }}
        {{- . | toYaml | nindent 8 }}
        {{- end }}
      annotations:
        {{- if $userDeployments.enabled }}
        checksum/dagster-workspace: {{ include (print $.Template.BasePath "/configmap-workspace.yaml") . | sha256sum }}
        {{- end }}
        checksum/dagster-instance: {{ include (print $.Template.BasePath "/configmap-instance.yaml") . | sha256sum }}
        {{- range $key, $value := .Values.dagit.annotations }}
        {{ $key }}: {{ $value | squote }}
        {{- end }}
    spec:
    {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
    {{- end }}
      serviceAccountName: {{ include "dagster.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.dagit.podSecurityContext | nindent 8 }}
      initContainers:
        - name: check-db-ready
          image: {{ include "dagster.externalImage.name" .Values.postgresql.image | quote }}
          imagePullPolicy: {{ .Values.postgresql.image.pullPolicy }}
          command: ['sh', '-c', {{ include "dagster.postgresql.pgisready" . | squote }}]
          securityContext:
            {{- toYaml .Values.dagit.securityContext | nindent 12 }}
        {{- if (and $userDeployments.enabled $userDeployments.enableSubchart) }}
        {{- range $deployment := $userDeployments.deployments }}
        - name: "init-user-deployment-{{- $deployment.name -}}"
          image: {{ include "dagster.externalImage.name" $.Values.busybox.image | quote }}
          command: ['sh', '-c', "until nslookup {{ $deployment.name -}}; do echo waiting for user service; sleep 2; done"]
        {{- end }}
        {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.dagit.securityContext | nindent 12 }}
          imagePullPolicy: {{ .Values.dagit.image.pullPolicy }}
          image: {{ include "dagster.dagsterImage.name" (list $ .Values.dagit.image) | quote }}
          command: [
            "/bin/bash",
            "-c",
            "{{ template "dagster.dagit.dagitCommand" . }}"
          ]
          env:
            - name: DAGSTER_PG_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ include "dagster.postgresql.secretName" . | quote }}
                  key: postgresql-password
          envFrom:
            - configMapRef:
                name: {{ template "dagster.fullname" . }}-dagit-env
            {{- range $envConfigMap := .Values.dagit.envConfigMaps }}
            - configMapRef: {{- $envConfigMap | toYaml | nindent 16 }}
            {{- end }}
            {{- range $envSecret := .Values.dagit.envSecrets }}
            - secretRef: {{- $envSecret | toYaml | nindent 16 }}
            {{- end }}
            {{- if eq $.Values.runLauncher.type "CeleryK8sRunLauncher" }}
            - secretRef:
                name: {{ $.Values.global.celeryConfigSecretName }}
            {{- end }}
          volumeMounts:
            - name: dagster-instance
              mountPath: "{{ .Values.global.dagsterHome }}/dagster.yaml"
              subPath: dagster.yaml
            {{- if $userDeployments.enabled }}
            # Do not use `subPath` to allow the configmap to update if modified
            - name: dagster-workspace-yaml
              mountPath: "/dagster-workspace/"
            {{- end }}
          ports:
            - name: http
              containerPort: {{ .Values.dagit.service.port }}
              protocol: TCP
          resources:
            {{- toYaml .Values.dagit.resources | nindent 12 }}
        {{- if .Values.dagit.readinessProbe }}
          readinessProbe:
            {{- toYaml .Values.dagit.readinessProbe | nindent 12 }}
        {{- end }}
        {{- if .Values.dagit.livenessProbe }}
          livenessProbe:
            {{- toYaml .Values.dagit.livenessProbe | nindent 12 }}
        {{- end }}
        {{- if .Values.dagit.startupProbe.enabled}}
          {{- $startupProbe := omit .Values.dagit.startupProbe "enabled" }}
          startupProbe:
            {{- toYaml $startupProbe | nindent 12 }}
        {{- end }}
      {{- with .Values.dagit.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}

      volumes:
        - name: dagster-instance
          configMap:
            name: {{ template "dagster.fullname" . }}-instance
        {{- if $userDeployments.enabled }}
        - name: dagster-workspace-yaml
          configMap:
            name: {{ include "dagit.workspace.configmapName" . }}
        {{- end }}
    {{- with .Values.dagit.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    {{- with .Values.dagit.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    {{- if .Values.dagit.schedulerName }}
      schedulerName: {{ .Values.dagit.schedulerName }}
    {{- end }}


{{ end }}
