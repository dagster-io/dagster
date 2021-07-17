# start_dependencies_marker

brew install kubectl helm

# end_dependencies_marker

# start_kubectl_config_marker

kubectl config set-context dagster --namespace default --cluster docker-desktop --user=docker-desktop
kubectl config use-context dagster

# end_kubectl_config_marker

# start_helm_repo_marker

helm repo add dagster https://dagster-io.github.io/helm

helm show values dagster/dagster > values.yaml
helm upgrade --install dagster dagster/dagster -f values.yaml

# end_helm_repo_marker

# start_dagit_pod_marker

export DAGIT_POD_NAME=$(kubectl get pods --namespace default \
  -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster,component=dagit" \
  -o jsonpath="{.items[0].metadata.name}")

# end_dagit_pod_marker

# start_port_forward_marker

kubectl --namespace default port-forward $DAGIT_POD_NAME 8080:80

# end_port_forward_marker
