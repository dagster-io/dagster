# dagster-k8s

Utilities for running Dagster with Kubernetes. This includes a Python API allowing Dagit to launch
runs as Kubernetes Jobs, as well as a Helm chart you can use as the basis for a Dagster deployment
on a Kubernetes cluster.

## Python API

The `K8sRunLauncher` allows Dagit instances to be configured to launch new runs by starting per-run
Kubernetes Jobs. To configure the `K8sRunLauncher`, your `dagster.yaml` should include a section
like:

```yaml
run_launcher:
    module: dagster_k8s.launcher
    class: K8sRunLauncher
    config:
    {{- with .Values.imagePullSecrets }}
    image_pull_secrets:
        {{- toYaml . | nindent 10 }}
    {{- end }}
    service_account_name: dagster
    job_image: "d"
    instance_config_map: "{{ template "dagster.fullname" .}}-instance"
```

## Helm chart

For local dev (e.g., on kind or minikube):

    helm install \
        --set dagit.image.repository="dagster-docker-buildkite" \
        --set dagit.image.tag="py37-latest" \
        --set job_runner.image.repository="dagster.io/dagster-docker-buildkite" \
        --set job_runner.image.tag="py37-latest" \
        --set imagePullPolicy="IfNotPresent" \
    dagster \
    helm/dagster/

Port-forward dagit with something like:

    export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster" -o jsonpath="{.items[0].metadata.name}")
    kubectl --namespace default port-forward $POD_NAME 8080:80

## Running tests

To run the unit tests:

    pytest -m "not integration"

To run the integration tests, you must have [Docker](https://docs.docker.com/install/),
[kind](https://kind.sigs.k8s.io/docs/user/quick-start#installation),
and [helm](https://helm.sh/docs/intro/install/) installed.

On OS X:

    brew install kind
    brew install helm

Docker must be running.

You may experience slow first test runs thanks to image pulls (run `pytest -svv --fulltrace` for
visibility). Building images and loading them to the kind cluster is slow, and there is
no visibility into the progress of the load.

### Faster local development

You may find that the kind cluster creation, image loading, and kind cluster creation loop
is too slow for effective local dev.

You may bypass cluster creation and image loading in the following way.

First, ensure you have a Docker image appropriate for your Python version. Run, from the root of
the repo:

    ./.buildkite/images/docker/test_project/build.sh 3.7.6
    docker tag dagster-docker-buildkite:latest \
        dagster.io/dagster-docker-buildkite:py37-latest

In the above invocation, the Python majmin version should be appropriate for your desired tests.

Then run the following commands to create the cluster and load the image. Note that there is no
feedback from the loading process.

    kind create cluster --name kind-test
    kind load docker-image --name kind-test dagster.io/dagster-docker-buildkite:py37-latest

If you are deploying the Helm chart with an in-cluster Postgres (rather than an external database),
and/or with dagster-celery workers (and a RabbitMQ), you'll also want to have images present for
rabbitmq and postgresql:

    docker pull docker.io/bitnami/rabbitmq
    docker pull docker.io/bitnami/postgresql

    kind load docker-image --name kind-test docker.io/bitnami/rabbitmq:latest
    kind load docker-image --name kind-test docker.io/bitnami/postgresql:latest

Then you can run pytest as follows:

    pytest --cluster=kind-test

This will bypass the cluster creation/deletion step, and you will incur the image load overhead
only when the image changes, at the expense of each test run executing in a fully isolated cluster.
Note that the Helm chart will still be uninstalled at the end of each test run making use of the
chart.

For kubectl to work with the kind cluster, run:

    kind get kubeconfig --name kind-test > kubeconfig
    export KUBECONFIG=`pwd`/kubeconfig

### Validating helm charts

To test / validate Helm charts, you can run:

```shell
helm install dagster --dry-run --debug helm/dagster
helm lint
```

### Enabling GCR access from Minikube

To enable GCR access from Minikube:

```
kubectl create secret docker-registry element-dev-key \
    --docker-server=https://gcr.io \
    --docker-username=oauth2accesstoken \
    --docker-password="$(gcloud auth print-access-token)" \
    --docker-email=my@email.com
```

## A note about PVCs

Both the Postgres and the RabbitMQ Helm charts will store credentials using Persistent Volume
Claims, which will outlive test invocations and calls to `helm uninstall`. These must be deleted if
you want to change credentials. To view your pvcs, run:

    kubectl get pvc
