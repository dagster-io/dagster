from buildkite_shared.step_builders.command_step_builder import ResourceRequests

# Shared by every test step that spins up a kind (kubernetes-in-docker) cluster
# inside the dind sidecar — `validating-admission-webhook-e2e-testing`,
# `k8s-test-suite`, `celery-k8s-test-suite`. kind hosts apiserver, etcd,
# controller-manager, scheduler, kubelet, and the workload pods all inside a
# single "node" container, so the dind sidecar's 1Gi req / 2Gi limit default
# OOMs under load.
KIND_TEST_RESOURCES = ResourceRequests(
    cpu="1500m",
    memory="2Gi",
    docker_cpu="2000m",
    # docker_memory_limit covers the working set of every process running
    # inside dind: kind's etcd + apiserver + scheduler + controller-manager
    # + kubelet, plus the 10 workload pods (postgres, rabbitmq, redis,
    # 3 celery workers, webserver, daemon, user-code, flower, localstack).
    docker_memory="4Gi",
    docker_memory_limit="10Gi",
    # Dedicated emptyDir at /var/lib/docker. Removes one overlayfs layer
    # (dind container's writable layer) for `kind load docker-image` and
    # local-path-provisioner PVC binding. Backed by EBS, not RAM -- a tmpfs
    # here competes with the dind sidecar's memory cgroup as containerd
    # accumulates terminated dagster-run-* pod state.
    docker_storage_size="20Gi",
    # 30Gi: 20Gi for the /var/lib/docker emptyDir + 10Gi headroom for the
    # agent's checkout, build artifacts, container writable layer, and pod
    # log capture. Pod ephemeral_storage must cover every emptyDir sizeLimit
    # plus container writable layers, or kubelet evicts.
    ephemeral_storage="30Gi",
)
