---
title: "Deploy to Kubernetes"
sidebar_position: 21
---

Deploying Dagster to a Kubernetes cluster is a popular option for maintaining a production Dagster deployment. Dagster uses Helm, a package manager for Kubernetes applications, to help manage deploying Dagster to a Kubernetes cluster.

Dagster provides [Helm charts](https://github.com/dagster-io/dagster/tree/master/helm) for deploying Dagster that you can customize for your specific needs. For each Dagster component used by the Helm chart, Dagster publishes a corresponding image to [DockerHub](https://hub.docker.com/u/dagster).

## What you'll learn

- How to get your Dagster project ready to deploy to your Kubernetes cluster
- How to build a Docker image containing your Dagster project to deploy to your cluster
- How to access and customize the Dagster-provided Helm charts
- How to apply the configuration in the Helm charts to your Kubernetes cluster to deploy your Dagster project
- How to connect to your deployed Dagster project

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- **Familiarity with [Docker](https://docs.docker.com/)**, and:
  - **To have Docker installed**. [Docker installation guide](https://docs.docker.com/engine/install/)
  - **Access to a Docker image registry**, such as Amazon Web Services ECR or DockerHub. If you're following along on your local machine, this isn't required.
- **Familiarity with [Kubernetes](https://kubernetes.io/docs/home/)**, and:
  - **To have `kubectl` installed**. [Kubernetes installation guide](https://kubernetes.io/docs/tasks/tools/)
  - **An existing Kubernetes cluster**. To follow along on your local machine, [install Docker Desktop](https://docs.docker.com/desktop/kubernetes/) and turn on the included Kubernetes server.
- **Familiarity with [Helm](https://helm.sh/docs/)**, and:
  - **To have Helm 3 installed**. [Helm installation guide](https://helm.sh/docs/intro/install/)
- A Dagster project to deploy. You can also use the [example project](/todo):
  ```bash
  dagster project from-example --example deploy_k8s_beta --name deploy_k8s_beta
  ```

</details>

## Step 1: Prepare your Dagster project
You will need to add a `workspace.yaml` file to your Dagster project to be ready to deploy with Kubernetes. If you are using the [example project](/todo), you will already have this file.

The `workspace.yaml` file tells Dagster where to find the `Definitions` object in your project. This file should be at the LOCATION of your project.

<CodeExample filePath="guides/deployment/kubernetes/workspace.yaml" language="yaml" title="Example workspace.yaml" />
For example, in the sample `iris_analysis` project, the `Definitions` object is found in the `iris_analysis/__init__.py` file. The `workspace.yaml` tells Dagster to load this project and give it the name `iris_analysis`.

You can also point to a Python module in the `workspace.yaml` file. To learn more about writing a `workspace.yaml` see the [Workspace](/todo) guide.

## Step 2: Write and build a Docker image containing your Dagster project
### Step 2.1: Write a Dockerfile
Next, you'll build a Docker image that contains your Dagster project and all of its dependencies. The Dockerfile should:
1. Copy your Dagster project, including the `workspace.yaml` file created in Step 1, into the image.
2. Install `dagster`, `dagster-postgres`, and `dagster-k8s`, along with any other libraries your project depends on. The example project has a dependency on `pandas` so it's included in the `pip install` in the following example Dockerfile.
3. Expose port 80, which we'll use to set up port-forwarding later.

<CodeExample filePath="guides/deployment/kubernetes/Dockerfile" language="docker" title="Example Dockerfile" />


### Step 2.2: Build and push a Docker image

To build your Docker image, run the following command from the directory where your Dockerfile is located:

```bash
docker build . -t iris_analysis:1
```
This builds the Docker image from Step 2.1 and gives it the name `iris_analysis` and tag `1`. You can set custom values for both the name and the tag. We recommend that each time you rebuild your Docker image, you assign a new value for the tag to ensure that the correct image is used when running your code.


If you are using a Docker image registry, push the image to your registry. If you are following along on your local machine, you can skip this command.

```bash
docker push iris_analysis:1
```

TODO - specific instructions if pushing to an image registry?


## Step 3: Configure `kubectl` to point at a Kubernetes cluster
Before you can deploy Dagster, you need to configure `kubectl` to develop against the Kubernetes cluster where you want Dagster to be deployed.

If you are using Docker Desktop and the included Kubernetes server, you will need to create a context first. If you already have a Kubernetes cluster and context created for your Dagster deployment you can skip running this command.
```bash
kubectl config set-context dagster --namespace default --cluster docker-desktop --user=docker-desktop
```

Ensure that `kubectl` is using the correct context by running:
```bash
kubectl config use-context <context-name>
```
Where `<context-name>` is the name of the context you want to use. For example, if you ran the preceding `kubectl config set-context` command, you will run
```bash
kubectl config use-context dagster
```

## Step 4: Add the Dagster Helm chart repository

Dagster publishes [Helm charts](https://artifacthub.io/packages/helm/dagster/dagster) for deploying Dagster, with a new chart for each Dagster version.

To install the Dagster Helm charts, run the following command:

```bash
helm repo add dagster https://dagster-io.github.io/helm
```

If you have previously added the Dagster Helm charts, run the following command to update the repository:

```bash
helm repo update
```

## Step 5: Configure the Helm chart for your deployment

You will need to modify some values in Dagster's Helm chart to deploy your Dagster project.

### Step 5.1: Copy default Helm chart values into values.yaml

Run the following command to copy the values installed from the published Helm charts:

```bash
helm show values dagster/dagster > values.yaml
```
TODO - where to copy this file to?

### Step 5.2: Modify the `values.yaml` file for your deployment
The `values.yaml` file contains configuration options you can set for your deployment. Different configuration options are explained in inline comments in `values.yaml`, and you can learn more about the different configuration options in [The title of a guide explaining it](/todo).

To deploy your project, you'll need to set the following options:
- `deployments.name`, which should be a unique name for your deployment
- `deployments.image.name` and `deployments.image.tag`, which should be set to match the Docker image from Step 2
- `deployments.dagsterApiGrpcArgs`, which should be set to NEED HELP WITH HOW TO EXPLAIN THIS.

If you are following this guide on your local machine, you will also need to set `pullPolicy: IfNotPresent`. This will use the local version of the image built in Step 2. However, in production use cases when your Docker images are pushed to image registries, this value should remain `pullPolicy: Always`.

<CodeExample filePath="guides/deployment/kubernetes/minimal_values.yaml" language="yaml" title="Minimal changes to make to values.yaml" />



## Step 6: Install the Helm chart
Now that you have modified the Helm `values.yaml` file, you can install the changes in your Kubernetes cluster.

Run the following command to install the Helm chart and create a release (TODO i dont really know what create a release means in this context, just took it from the existing guide)

```bash
helm upgrade --install dagster dagster/dagster -f /path/to/values.yaml
```
I think it would be nice to explain the various components of this command and what to set them to, but i dont know what the command is really doing

:::note
If you are running an older version of Dagster, pass the `--version` flag to `helm upgrade` with the version of Dagster you are running. For example, if you are running `dagster==1.7.4` you'll run the command `helm upgrade --install dagster dagster/dagster -f /path/to/values.yaml --version 1.7.4`
:::

The `helm upgrade` command will launch several pods in your Kubernetes cluster. You can check the status of the pod with the command:

```bash
kubectl get pods
```

It may take a few minutes before all pods are in a `RUNNING` state. If the `helm upgrade` was successful, you should see a `kubectl get pods` output similar to this:

```bash
$ kubectl get pods
NAME                                                              READY   STATUS      AGE
dagster-daemon-5787ccc868-nsvsg                                   1/1     Running     3m41s
dagster-webserver-7c5b5c7f5c-rqrf8                                1/1     Running     3m41s
dagster-dagster-user-deployments-iris-analysis-564cbcf9f-fbqlw    1/1     Running     3m41s
dagster-postgresql-0                                              1/1     Running     3m41s
```

<details>
  <summary>Debugging failed pods</summary>

If one of the pods is in an error state, you can view the logs using the command

```bash
kubectl logs <pod-name>
```

For example, if the pod `dagster-webserver-7c5b5c7f5c-rqrf8` is in a `CrashLoopBackOff` state, the logs can be viewed with the command

```
kubectl logs dagster-webserver-7c5b5c7f5c-rqrf8
```

</details>

TODO - maybe explain what each of these pods are?

## Step 7: Connect to your Dagster deployment and materialize your assets

### Step 7.1: Start port-forwarding to the webserver pod
Run the following command to set up port forwarding to the webserver pod:

```bash
DAGSTER_WEBSERVER_POD_NAME=$(kubectl get pods --namespace default \
  -l "app.kubernetes.io/name=dagster,app.kubernetes.io/instance=dagster,component=dagster-webserver" \
  -o jsonpath="{.items[0].metadata.name}")
kubectl --namespace default port-forward $DAGSTER_WEBSERVER_POD_NAME 8080:80
```

This command gets the full name of the `webserver` pod from the output of `kubectl get pods`, and then sets up port forwarding with the `kubectl port-forward` command.

### Step 7.2: Visit your Dagster deployment
The webserver has been port-forwarded to `8080`, so you can visit the Dagster deployment by going to [http://127.0.0.1:8080](http://127.0.0.1:8080). You should see the Dagster landing page

TODO SCREENSHOT


### Step 7.3: Materialize an asset
In the Dagster UI, navigate to the Asset catalog and click the **Materialize** button to materialize an asset. Dagster will start a Kubernetes job to materialize the asset. You can introspect on the Kubernetes cluster to see this job:


```bash
$ kubectl get jobs
NAME                                               COMPLETIONS   DURATION   AGE
dagster-run-5ee8a0b3-7ca5-44e6-97a6-8f4bd86ee630   1/1           4s         11s
```


## Next steps
- Forwarding Dagster logs from a Kubernetes deployment to AWS, Azure, GCP
- Other configuration options for K8s deployment - secrets,
