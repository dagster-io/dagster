
Kubernetes (dagster_k8s)
------------------------
See also the `Kubernetes deployment guide <https://docs.dagster.io/deploying/k8s_part1/>`_.

This library contains utilities for running Dagster with Kubernetes. This includes a Python API
allowing Dagit to launch runs as Kubernetes Jobs, as well as a Helm chart you can use as the basis
for a Dagster deployment on a Kubernetes cluster.

APIs
----
.. currentmodule:: dagster_k8s

.. autoclass:: K8sRunLauncher

.. currentmodule:: dagster_k8s

.. autoclass:: K8sScheduler


Python API
^^^^^^^^^^

The ``K8sRunLauncher`` allows Dagit instances to be configured to launch new runs by starting per-run
Kubernetes Jobs. To configure the ``K8sRunLauncher``\ , your ``dagster.yaml`` should include a section
like:

.. code-block:: yaml

   run_launcher:
     module: dagster_k8s.launcher
     class: K8sRunLauncher
     config:
       image_pull_secrets:
       service_account_name: dagster
       job_image: "my-company.com/image:latest"
       dagster_home: "/opt/dagster/dagster_home"
       postgres_password_secret: "dagster-postgresql-secret"
       image_pull_policy: "IfNotPresent"
       job_namespace: "dagster"
       instance_config_map: "dagster-instance"
       env_config_maps:
         - "dagster-k8s-job-runner-env"
       env_secrets:
         - "dagster-k8s-some-secret"

Helm chart
^^^^^^^^^^

For local dev (e.g., on kind or minikube):

.. code-block:: shell

   helm install \
       --set dagit.image.repository="dagster.io/dagster-docker-buildkite" \
       --set dagit.image.tag="py37-latest" \
       --set job_runner.image.repository="dagster.io/dagster-docker-buildkite" \
       --set job_runner.image.tag="py37-latest" \
       --set imagePullPolicy="IfNotPresent" \
       dagster \
       helm/dagster/

Upon installation, the Helm chart will provide instructions for port forwarding Dagit and Flower (if
configured).

Running tests
^^^^^^^^^^^^^

To run the unit tests:

.. code-block::

   pytest -m "not integration"


To run the integration tests, you must have `Docker <https://docs.docker.com/install/>`_\ ,
`kind <https://kind.sigs.k8s.io/docs/user/quick-start#installation>`_\ ,
and `helm <https://helm.sh/docs/intro/install/>`_ installed.

On macOS:

.. code-block::

   brew install kind
   brew install helm

Docker must be running.

You may experience slow first test runs thanks to image pulls (run ``pytest -svv --fulltrace`` for
visibility). Building images and loading them to the kind cluster is slow, and there is
no visibility into the progress of the load.

**NOTE:** This process is quite slow, as it requires bootstrapping a local ``kind`` cluster with Docker images and the ``dagster-k8s`` Helm chart. For faster development, you can either:


#. Keep a warm kind cluster
#. Use a remote K8s cluster, e.g. via AWS EKS or GCP GKE

Instructions are below.

Faster local development (with kind)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may find that the kind cluster creation, image loading, and kind cluster creation loop
is too slow for effective local dev.

You may bypass cluster creation and image loading in the following way. First add the ``--no-cleanup``
flag to your pytest invocation:

.. code-block:: shell

   pytest --no-cleanup -s -vvv -m "not integration"

The tests will run as before, but the kind cluster will be left running after the tests are completed.

For subsequent test runs, you can run:

.. code-block:: shell

   pytest --kind-cluster="cluster-d9971c84d44d47f382a2928c8c161faa" --existing-helm-namespace="dagster-test-95590a" -s -vvv -m "not integration"

This will bypass cluster creation, image loading, and Helm chart installation, for much faster tests.

The kind cluster name and Helm namespace for this command can be found in the logs, or retrieved via the respective CLIs, using ``kind get clusters`` and ``kubectl get namespaces``. Note that for ``kubectl`` and ``helm`` to work correctly with a kind cluster, you should override your kubeconfig file location with:

.. code-block:: shell

   kind get kubeconfig --name kind-test > /tmp/kubeconfig
   export KUBECONFIG=/tmp/kubeconfig

Manual kind cluster setup
~~~~~~~~~~~~~~~~~~~~~~~~~

The test fixtures provided by ``dagster-k8s`` automate the process described below, but sometimes its useful to manually configure a kind cluster and load images onto it.

First, ensure you have a Docker image appropriate for your Python version. Run, from the root of
the repo:

.. code-block:: shell

   ./python_modules/dagster-test/dagster_test/test_project/build.sh 3.7.6 \
       dagster.io.priv/dagster-docker-buildkite:py37-latest

In the above invocation, the Python majmin version should be appropriate for your desired tests.

Then run the following commands to create the cluster and load the image. Note that there is no
feedback from the loading process.

.. code-block:: shell

   kind create cluster --name kind-test
   kind load docker-image --name kind-test dagster.io/dagster-docker-buildkite:py37-latest

If you are deploying the Helm chart with an in-cluster Postgres (rather than an external database),
and/or with dagster-celery workers (and a RabbitMQ), you'll also want to have images present for
rabbitmq and postgresql:

.. code-block:: shell

   docker pull docker.io/bitnami/rabbitmq
   docker pull docker.io/bitnami/postgresql

   kind load docker-image --name kind-test docker.io/bitnami/rabbitmq:latest
   kind load docker-image --name kind-test docker.io/bitnami/postgresql:latest

Then you can run pytest as follows:

.. code-block:: shell

   pytest --kind-cluster=kind-test

Faster local development (with an existing K8s cluster)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you already have a development K8s cluster available, you can run tests on that cluster vs. running locally in ``kind``.

For this to work, first build and deploy the test image to a registry available to your cluster. For example, with ECR:

.. code-block::

   ./python_modules/dagster-test/dagster_test/test_project/build.sh 3.7.6
   docker tag dagster-docker-buildkite:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-1.amazonaws.com/dagster-k8s-tests:2020-04-21T21-04-06

   aws ecr get-login --no-include-email --region us-west-1 | sh
   docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-1.amazonaws.com/dagster-k8s-tests:2020-04-21T21-04-06

Then, you can run tests on EKS with:

.. code-block::

   export DAGSTER_DOCKER_IMAGE_TAG="2020-04-21T21-04-06"
   export DAGSTER_DOCKER_REPOSITORY="$AWS_ACCOUNT_ID.dkr.ecr.us-west-1.amazonaws.com"
   export DAGSTER_DOCKER_IMAGE="dagster-k8s-tests"

   # First run with --no-cleanup to leave Helm chart in place
   pytest --cluster-provider="kubeconfig" --no-cleanup -s -vvv

   # Subsequent runs against existing Helm chart
   pytest --cluster-provider="kubeconfig" --existing-helm-namespace="dagster-test-<some id>" -s -vvv

Validating Helm charts
^^^^^^^^^^^^^^^^^^^^^^

To test / validate Helm charts, you can run:

.. code-block:: shell

   helm install dagster --dry-run --debug helm/dagster
   helm lint

Enabling GCR access from Minikube
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To enable GCR access from Minikube:

.. code-block:: shell

   kubectl create secret docker-registry element-dev-key \
       --docker-server=https://gcr.io \
       --docker-username=oauth2accesstoken \
       --docker-password="$(gcloud auth print-access-token)" \
       --docker-email=my@email.com

A note about PVCs
^^^^^^^^^^^^^^^^^

Both the Postgres and the RabbitMQ Helm charts will store credentials using Persistent Volume
Claims, which will outlive test invocations and calls to ``helm uninstall``. These must be deleted if
you want to change credentials. To view your pvcs, run:

.. code-block::

   kubectl get pvc


Testing Redis
^^^^^^^^^^^^^

The Redis Helm chart installs w/ a randomly-generated password by default; turn this off:

.. code-block::

   helm install dagredis stable/redis --set usePassword=false

Then, to connect to your database from outside the cluster execute the following commands:

.. code-block::

   kubectl port-forward --namespace default svc/dagredis-master 6379:6379
   redis-cli -h 127.0.0.1 -p 6379
