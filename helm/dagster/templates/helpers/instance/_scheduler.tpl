{{- define "dagsterYaml.scheduler.daemon" }}
module: dagster.core.scheduler
class: DagsterDaemonScheduler
{{- end }}

{{- define "dagsterYaml.scheduler.k8s" }}
{{- $k8sSchedulerConfig := .Values.scheduler.config.k8sScheduler }}
module: dagster_k8s.scheduler
class: K8sScheduler
config:
  load_incluster_config: {{ $k8sSchedulerConfig.loadInclusterConfig }}
  scheduler_namespace: {{ $k8sSchedulerConfig.schedulerNamespace | default .Release.Namespace | quote }}
  {{- if $k8sSchedulerConfig.kubeconfigFile }}
  kubeconfig_file: {{ $k8sSchedulerConfig.kubeconfigFile | quote }}
  {{- end }}
  image_pull_secrets: {{- toYaml $.Values.imagePullSecrets | nindent 4 }}
  service_account_name: {{ include "dagster.serviceAccountName" . }}
  job_image: {{ include "dagster.dagsterImage.name" (list $ $k8sSchedulerConfig.image) }}
  image_pull_policy: {{ $k8sSchedulerConfig.image.pullPolicy }}
  dagster_home:
    env: DAGSTER_HOME
  postgres_password_secret:
    env: DAGSTER_K8S_PG_PASSWORD_SECRET
  instance_config_map:
    env: DAGSTER_K8S_INSTANCE_CONFIG_MAP
  env_config_maps:
    - env: DAGSTER_K8S_PIPELINE_RUN_ENV_CONFIGMAP

  {{- if $k8sSchedulerConfig.envSecrets }}
  env_secrets:
    {{- range $envSecret := $k8sSchedulerConfig.envSecrets }}
    {{- if hasKey $envSecret "name" }}
    - {{ $envSecret.name }}
    {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{- define "dagsterYaml.scheduler.custom" }}
{{- $customSchedulerConfig := .Values.scheduler.config.customScheduler }}
module: {{ $customSchedulerConfig.module | quote }}
class: {{ $customSchedulerConfig.class | quote }}
config: {{ $customSchedulerConfig.config | toYaml | nindent 2 }}
{{- end }}