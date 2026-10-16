from dagster import Field, Permissive, StringSource

# Mirrors dagster_azure.container_apps.SHARED_ACA_SCHEMA so the workspace schema does not import
# dagster-azure; a test keeps the two in sync.
SHARED_ACA_CONFIG = {
    "env_vars": Field(
        [StringSource],
        is_required=False,
        description=(
            "Environment variable names to forward to the ACA Job. "
            "Entries of the form KEY=VALUE set the value literally; a bare KEY "
            "inherits from the current process's environment."
        ),
    ),
    "run_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description=(
                        "CPU for the run container (decimal cores or "
                        'millicpus, e.g. "0.5" or "500m").'
                    ),
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description='Memory for the run container (e.g. "1Gi", "512Mi").',
                ),
            }
        ),
        is_required=False,
    ),
    "run_job_replica_timeout": Field(
        int,
        is_required=False,
        description=(
            "How long ACA allows the Job's single replica to run before "
            "forcibly terminating it, in seconds. Azure requires a value; when "
            "unset here and on the code location, the run launcher uses 24 hours."
        ),
    ),
    "server_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description='CPU for the code server container (e.g. "0.5" or "500m").',
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description='Memory for the code server container (e.g. "1Gi").',
                ),
            }
        ),
        is_required=False,
        description=(
            "Resource overrides applied when the ACA primitive is used for "
            "long-lived code servers (consumed by the dagster-cloud user code "
            "launcher). Ignored by the run launcher."
        ),
    ),
    "identity_id": Field(
        StringSource,
        is_required=False,
        description=(
            "Full ARM resource ID of a user-assigned managed identity to attach to "
            "the launched Job. ACA Jobs and Container Apps use this identity to pull "
            "images from Azure Container Registry — no registry credentials are stored "
            "on the agent. If unset, the Job runs with the system-assigned identity "
            "(if enabled on the environment)."
        ),
    ),
}


ACA_CONTAINER_CONTEXT_CONFIG = {**SHARED_ACA_CONFIG}
