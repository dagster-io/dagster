{{ define "deployment-webserver" }}
{{- $_ := include "dagster.backcompat" . | mustFromJson -}}
{{- $userDeployments := index .Values "dagster-user-deployments" }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ template "dagster.webserver.fullname" . }}
  labels:
    {{- include "dagster.labels" . | nindent 4 }}
    component: {{ include "dagster.webserver.componentName" . }}
    {{- with $_.Values.dagsterWebserver.deploymentLabels }}
    {{- . | toYaml | nindent 4 }}
    {{- end }}
  annotations:
    {{- range $key, $value := $_.Values.dagsterWebserver.annotations }}
    {{ $key }}: {{ $value | squote }}
    {{- end }}
spec:
  replicas: {{ $_.Values.dagsterWebserver.replicaCount }}
  selector:
    matchLabels:
      {{- include "dagster.selectorLabels" . | nindent 6 }}
      component: {{ include "dagster.webserver.componentName" . }}
  template:
    metadata:
      labels:
        {{- include "dagster.selectorLabels" . | nindent 8 }}
        component: {{ include "dagster.webserver.componentName" . }}
        {{- with $_.Values.dagsterWebserver.labels }}
        {{- . | toYaml | nindent 8 }}
        {{- end }}
      annotations:
        {{- if $userDeployments.enabled }}
        checksum/dagster-workspace: {{ include (print $.Template.BasePath "/configmap-workspace.yaml") . | sha256sum }}
        {{- end }}
        checksum/dagster-instance: {{ include (print $.Template.BasePath "/configmap-instance.yaml") . | sha256sum }}
        {{- range $key, $value := $_.Values.dagsterWebserver.annotations }}
        {{ $key }}: {{ $value | squote }}
        {{- end }}
    spec:
    {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
    {{- end }}
      serviceAccountName: {{ include "dagster.serviceAccountName" . }}
      automountServiceAccountToken: true
      securityContext:
        {{- toYaml $_.Values.dagsterWebserver.podSecurityContext | nindent 8 }}
      initContainers:
        - name: check-db-ready
          image: {{ include "dagster.externalImage.name" .Values.postgresql.image | quote }}
          imagePullPolicy: {{ .Values.postgresql.image.pullPolicy }}
          command: ['sh', '-c', {{ include "dagster.postgresql.pgisready" . | squote }}]
          securityContext:
            {{- toYaml $_.Values.dagsterWebserver.securityContext | nindent 12 }}
          {{- if $_.Values.dagsterWebserver.initContainerResources }}
          resources:
            {{- toYaml $_.Values.dagsterWebserver.initContainerResources | nindent 12 }}
          {{- end }}
        {{- if (and $userDeployments.enabled $userDeployments.enableSubchart) }}
        {{- range $deployment := $userDeployments.deployments }}
        - name: "init-user-deployment-{{- $deployment.name -}}"
          image: {{ include "dagster.externalImage.name" $.Values.busybox.image | quote }}
          command: ['sh', '-c', "until nslookup {{ $deployment.name -}}; do echo waiting for user service; sleep 2; done"]
          securityContext:
            {{- toYaml $_.Values.dagsterWebserver.securityContext | nindent 12 }}
          {{- if $_.Values.dagsterWebserver.initContainerResources }}
          resources:
            {{- toYaml $_.Values.dagsterWebserver.initContainerResources | nindent 12 }}
          {{- end }}
        {{- end }}
        {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml $_.Values.dagsterWebserver.securityContext | nindent 12 }}
          imagePullPolicy: {{ $_.Values.dagsterWebserver.image.pullPolicy }}
          image: {{ include "dagster.dagsterImage.name" (list $ $_.Values.dagsterWebserver.image) | quote }}
          command: [
            "/bin/bash",
            "-c",
            "{{ template "dagster.webserver.dagsterWebserverCommand" . }}"
          ]
          env:
            - name: DAGSTER_PG_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: {{ include "dagster.postgresql.secretName" . | quote }}
                  key: postgresql-password
            # This is a list by default, but for backcompat it can be a map. As
            # a map it's written to the webserver-env configmap.
            {{- if and ($_.Values.dagsterWebserver.env) (kindIs "slice" $_.Values.dagsterWebserver.env) }}
            {{- toYaml $_.Values.dagsterWebserver.env | nindent 12 }}
            {{- end}}
          envFrom:
            - configMapRef:
                name: {{ template "dagster.fullname" . }}-webserver-env
            {{- range $envConfigMap := $_.Values.dagsterWebserver.envConfigMaps }}
            - configMapRef: {{- $envConfigMap | toYaml | nindent 16 }}
            {{- end }}
            {{- range $envSecret := $_.Values.dagsterWebserver.envSecrets }}
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
            {{- if $_.Values.dagsterWebserver.volumeMounts }}
            {{- range $volumeMount := $_.Values.dagsterWebserver.volumeMounts }}
            - {{- $volumeMount | toYaml | nindent 14 }}
            {{- end }}
            {{- end }}
          ports:
            - name: http
              containerPort: {{ $_.Values.dagsterWebserver.service.port }}
              protocol: TCP
          resources:
            {{- toYaml $_.Values.dagsterWebserver.resources | nindent 12 }}
        {{- if $_.Values.dagsterWebserver.readinessProbe }}
          readinessProbe:
            {{- toYaml $_.Values.dagsterWebserver.readinessProbe | nindent 12 }}
        {{- end }}
        {{- if $_.Values.dagsterWebserver.livenessProbe }}
          livenessProbe:
            {{- toYaml $_.Values.dagsterWebserver.livenessProbe | nindent 12 }}
        {{- end }}
        {{- if $_.Values.dagsterWebserver.startupProbe.enabled}}
          {{- $startupProbe := omit $_.Values.dagsterWebserver.startupProbe "enabled" }}
          startupProbe:
            {{- toYaml $startupProbe | nindent 12 }}
        {{- end }}
      {{- with $_.Values.dagsterWebserver.nodeSelector }}
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
            name: {{ include "dagster.workspace.configmapName" . }}
        {{- end }}
        {{- if $_.Values.dagsterWebserver.volumes }}
        {{- range $volume := $_.Values.dagsterWebserver.volumes }}
        - {{- $volume | toYaml | nindent 10 }}
        {{- end }}
        {{- end }}
    {{- with $_.Values.dagsterWebserver.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    {{- with $_.Values.dagsterWebserver.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
    {{- end }}
    {{- if $_.Values.dagsterWebserver.schedulerName }}
      schedulerName: {{ $_.Values.dagsterWebserver.schedulerName }}
    {{- end }}


{{ end }}
