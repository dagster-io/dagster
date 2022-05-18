from dagster_buildkite.steps.integration import build_integration_steps


def build_dagster_oss_integration_steps():
    return build_integration_steps()
