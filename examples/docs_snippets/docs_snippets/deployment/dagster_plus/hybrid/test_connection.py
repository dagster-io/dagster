from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from dagster import DagsterInstance

try:
    from dagster_cloud_cli.core.graphql_client import create_agent_graphql_client
except ImportError:
    from dagster_cloud_cli.core.graphql_client import (
        create_proxy_client as create_agent_graphql_client,
    )

# Script that attempts to reproduce network issues connecting to Dagster+
# servers under load

NUM_TRIALS = 1000
CONCURRENCY = 5


def main():
    di = DagsterInstance.get()

    session = requests.Session()

    # Disable retries for the purpose of the test
    modified_client = create_agent_graphql_client(
        session,
        di.dagster_cloud_graphql_url,
        {**di._dagster_cloud_api_config, "retries": 0},
    )

    def _fetch():
        """Execute GraphQL query in a threadpool."""
        return modified_client.execute("query TestScriptQuery {__typename}")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        succeeded = 0
        failed = 0
        for f in as_completed(executor.submit(_fetch) for _ in range(NUM_TRIALS)):
            # Catch the error rather than crashing on the first failure, so that
            # the script can surface every connectivity error and report a rate
            try:
                f.result()
                succeeded += 1
                print(f"Trial succeeded ({succeeded} succeeded so far)")
            except Exception as e:
                failed += 1
                print(f"Trial failed: {e}")

    print(f"{succeeded} succeeded, {failed} failed out of {NUM_TRIALS}")


if __name__ == "__main__":
    main()
