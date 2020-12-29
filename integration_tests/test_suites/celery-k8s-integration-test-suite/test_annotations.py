import kubernetes
from marks import mark_daemon


@mark_daemon
def test_annotations(  # pylint: disable=redefined-outer-name,unused-argument
    dagster_instance_for_daemon, helm_namespace_for_daemon
):
    core_api = kubernetes.client.CoreV1Api()

    pods = core_api.list_namespaced_pod(namespace=helm_namespace_for_daemon).items
    services = core_api.list_namespaced_service(namespace=helm_namespace_for_daemon).items

    def check_annotation_values(k8s_objs, filter_str, expected_items, expected_annotation):
        matching = list(filter(lambda item: filter_str in item.metadata.name, k8s_objs))
        assert len(matching) == expected_items
        item = matching[0]
        annotations = item.metadata.annotations
        assert "dagster-integration-tests" in annotations
        assert annotations["dagster-integration-tests"] == expected_annotation

    check_annotation_values(pods, "dagit", 1, "dagit-pod-annotation")
    check_annotation_values(pods, "celery-workers", 3, "celery-pod-annotation")
    check_annotation_values(pods, "daemon", 1, "daemon-pod-annotation")
    check_annotation_values(pods, "user-code-deployment-1", 1, "ucd-1-pod-annotation")
    check_annotation_values(services, "dagit", 1, "dagit-svc-annotation")
    check_annotation_values(services, "user-code-deployment-1", 1, "ucd-1-svc-annotation")
