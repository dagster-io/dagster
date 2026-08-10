from dagster._core.test_utils import instance_for_test
from dagster_graphql.test.utils import execute_dagster_graphql, infer_repository_selector

from dagster_graphql_tests.graphql.repo_job_groups import (
    define_job_groups_test_out_of_process_context,
)

REPOSITORY_JOB_GROUPS_QUERY = """
query RepositoryJobGroupsQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
        __typename
        ... on Repository {
            pipelines {
                name
                groupName
            }
        }
    }
}
"""


def test_job_group_names_on_repository_jobs():
    with instance_for_test() as instance:
        with define_job_groups_test_out_of_process_context(instance) as context:
            result = execute_dagster_graphql(
                context,
                REPOSITORY_JOB_GROUPS_QUERY,
                variables={"repositorySelector": infer_repository_selector(context)},
            )

            assert not result.errors
            assert result.data
            assert result.data["repositoryOrError"]["__typename"] == "Repository"

            group_names_by_job = {
                job["name"]: job["groupName"]
                for job in result.data["repositoryOrError"]["pipelines"]
            }

            assert group_names_by_job["grouped_op_job"] == "operational/maintenance"
            assert group_names_by_job["grouped_asset_job"] == "analytics"
            # jobs defined without a group fall into the default group, as assets do
            assert group_names_by_job["ungrouped_op_job"] == "default"
