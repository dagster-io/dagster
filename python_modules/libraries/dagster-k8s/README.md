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
