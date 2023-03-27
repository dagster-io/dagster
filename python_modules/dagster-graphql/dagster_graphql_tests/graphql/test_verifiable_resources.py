from dagster_graphql.test.utils import (
    execute_dagster_graphql,
    infer_resource_selector,
)

TOP_LEVEL_RESOURCE_QUERY = """
query ResourceDetailsQuery($selector: ResourceSelector!) {
  topLevelResourceDetailsOrError(resourceSelector: $selector) {
    __typename
    ... on ResourceDetails {
        name
        description
        supportsVerification
        verificationResult {
            status
            message
        }
    }
  }
}
"""


def test_fetch_top_level_resource_no_verification(definitions_graphql_context, snapshot) -> None:
    selector = infer_resource_selector(definitions_graphql_context, name="my_outer_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["supportsVerification"] is False

    snapshot.assert_match(result.data)


def test_fetch_top_level_resource(definitions_graphql_context, snapshot) -> None:
    selector = infer_resource_selector(definitions_graphql_context, name="my_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]

    assert my_resource["supportsVerification"] is True
    assert my_resource["verificationResult"]["status"] == "NOT_RUN"

    snapshot.assert_match(result.data)


LAUNCH_VERIFICATION_MUTATION = """
  mutation($selector: ResourceSelector!) {
    launchResourceVerification(resourceSelector: $selector) {
      __typename
      ... on ResourceVerificationResult {
        status
        message
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
"""


def test_verify_resources_mutation(definitions_graphql_context, snapshot) -> None:
    selector = infer_resource_selector(definitions_graphql_context, name="my_resource")
    result = execute_dagster_graphql(
        definitions_graphql_context,
        LAUNCH_VERIFICATION_MUTATION,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["launchResourceVerification"]
    assert result.data["launchResourceVerification"]["__typename"] == "ResourceVerificationResult"
    assert result.data["launchResourceVerification"]["status"] == "SUCCESS"
    assert result.data["launchResourceVerification"]["message"] == "odd"

    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]
    assert my_resource["verificationResult"]["status"] == "SUCCESS"
    assert my_resource["verificationResult"]["message"] == "odd"

    result = execute_dagster_graphql(
        definitions_graphql_context,
        LAUNCH_VERIFICATION_MUTATION,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["launchResourceVerification"]
    assert result.data["launchResourceVerification"]["__typename"] == "ResourceVerificationResult"
    assert result.data["launchResourceVerification"]["status"] == "FAILURE"
    assert result.data["launchResourceVerification"]["message"] == "even"

    result = execute_dagster_graphql(
        definitions_graphql_context,
        TOP_LEVEL_RESOURCE_QUERY,
        {"selector": selector},
    )

    assert not result.errors
    assert result.data
    assert result.data["topLevelResourceDetailsOrError"]
    my_resource = result.data["topLevelResourceDetailsOrError"]
    assert my_resource["verificationResult"]["status"] == "FAILURE"
    assert my_resource["verificationResult"]["message"] == "even"
