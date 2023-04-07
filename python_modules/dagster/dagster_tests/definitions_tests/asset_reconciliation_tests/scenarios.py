from dagster import Definitions

from .auto_materialize_policy_scenarios import auto_materialize_policy_scenarios
from .basic_scenarios import basic_scenarios
from .exotic_partition_mapping_scenarios import exotic_partition_mapping_scenarios
from .freshness_policy_scenarios import freshness_policy_scenarios
from .partition_scenarios import partition_scenarios

ASSET_RECONCILIATION_SCENARIOS = {
    **exotic_partition_mapping_scenarios,
    **partition_scenarios,
    **basic_scenarios,
    **freshness_policy_scenarios,
    **auto_materialize_policy_scenarios,
}

# put repos in the global namespace so that the daemon can load them with LoadableTargetOrigin
for scenario_name, scenario in ASSET_RECONCILIATION_SCENARIOS.items():
    d = Definitions(
        assets=scenario.assets,
    )

    globals()["hacky_daemon_repo_" + scenario_name] = d.get_repository_def()
