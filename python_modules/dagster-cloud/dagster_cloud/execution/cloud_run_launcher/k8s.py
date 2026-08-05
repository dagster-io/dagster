from dagster_k8s import K8sRunLauncher


class CloudK8sRunLauncher(K8sRunLauncher):
    # Avoid call to `count_resume_run_attempts`, since resuming runs is not currently
    # supported in cloud and the method makes repeated event log calls.
    @property
    def supports_run_worker_crash_recovery(self):
        return False
