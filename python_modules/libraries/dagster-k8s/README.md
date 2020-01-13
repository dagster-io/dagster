# dagster-k8s

To enable GCR access from Minikube:

```
kubectl create secret docker-registry element-dev-key \
    --docker-server=https://gcr.io \
    --docker-username=oauth2accesstoken \
    --docker-password="$(gcloud auth print-access-token)" \
    --docker-email=my@email.com
```

To test / validate Helm charts, you can run:

```shell
helm install dagster --dry-run --debug .
helm lint
```

## Running tests

You must have [Docker](https://docs.docker.com/install/),
[kind](https://kind.sigs.k8s.io/docs/user/quick-start#installation),
and [helm](https://helm.sh/docs/intro/install/) installed. On OS X:

    brew install kind
    brew install helm

Docker must be running. You may experience slow first test runs thanks to image pulls (run
`pytest -sv --fulltrace` for visibility).
