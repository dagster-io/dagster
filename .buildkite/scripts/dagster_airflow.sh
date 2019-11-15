set -eu

TOX_PYTHON_VERSION="$1"

# Environment vars
export DAGSTER_AIRFLOW_DOCKER_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-airflow-demo:${BUILDKITE_BUILD_ID}"
export CLUSTER_NAME=kind`echo ${BUILDKITE_JOB_ID} | sed -e 's/-//g'`
export KUBECONFIG="/tmp/kubeconfig"
export AIRFLOW_HOME="/airflow"

# ensure cleanup happens on error or normal exit
function cleanup {
    kind delete cluster --name ${CLUSTER_NAME}
}
trap cleanup EXIT

# Need a unique cluster name for this job; can't have hyphens
kind create cluster --name ${CLUSTER_NAME}
kind get kubeconfig --internal --name ${CLUSTER_NAME} > ${KUBECONFIG}

# see https://kind.sigs.k8s.io/docs/user/private-registries/#use-an-access-token
for node in $(kubectl get nodes -oname); do
    # the -oname format is kind/name (so node/name) we just want name
    node_name=${node#node/}
    # copy the config to where kubelet will look
    docker cp $HOME/.docker/config.json ${node_name}:/var/lib/kubelet/config.json
    # restart kubelet to pick up the config
    docker exec ${node_name} systemctl restart kubelet.service
done

mkdir -p ${AIRFLOW_HOME}

# Finally, run tests
cd python_modules/dagster-airflow/
tox -e $TOX_PYTHON_VERSION
