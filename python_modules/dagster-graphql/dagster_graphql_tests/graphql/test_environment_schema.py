from dagster_graphql.test.utils import execute_dagster_graphql
from .setup import define_context, csv_hello_world_solids_config

ENVIRONMENT_SCHEMA_QUERY = '''
query($selector: ExecutionSelector! $mode: String!)
{
  environmentSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on EnvironmentSchema {
      rootEnvironmentType {
        name
      }
      allConfigTypes {
        name
      }
    }
  }
}
'''


def test_successful_enviroment_schema(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'multi_mode_with_resources'}, 'mode': 'add_mode'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'EnvironmentSchema'

    snapshot.assert_match(result.data)


def test_environment_schema_pipeline_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'jkdjfkdjfd'}, 'mode': 'add_mode'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'PipelineNotFoundError'


def test_environment_schema_solid_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={
            'selector': {'name': 'multi_mode_with_resources', 'solidSubset': ['kdjfkdj']},
            'mode': 'add_mode',
        },
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'SolidNotFoundError'


def test_environment_schema_mode_not_found():
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_QUERY,
        variables={'selector': {'name': 'multi_mode_with_resources'}, 'mode': 'kdjfdk'},
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'ModeNotFoundError'


ENVIRONMENT_SCHEMA_CONFIG_TYPE_QUERY = '''
query($selector: ExecutionSelector! $mode: String! $configTypeName: String!)
{
  environmentSchemaOrError(selector: $selector, mode: $mode){
    __typename
    ... on EnvironmentSchema {
      configTypeOrError(configTypeName: $configTypeName) {
        __typename
        ... on EnumConfigType {
          name
        }
        ... on RegularConfigType {
          name
        }
        ... on CompositeConfigType {
          name
        }
      }
    }
  }
}
'''


def test_success_config_type_fetch(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_CONFIG_TYPE_QUERY,
        variables={
            'selector': {'name': 'multi_mode_with_resources'},
            'mode': 'add_mode',
            'configTypeName': 'MultiModeWithResources.Mode.AddMode.Environment',
        },
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'EnvironmentSchema'
    assert (
        result.data['environmentSchemaOrError']['configTypeOrError']['__typename']
        == 'CompositeConfigType'
    )

    snapshot.assert_match(result.data)


def test_success_config_type_not_found(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_CONFIG_TYPE_QUERY,
        variables={
            'selector': {'name': 'multi_mode_with_resources'},
            'mode': 'add_mode',
            'configTypeName': 'jkdfjkdjfd',
        },
    )
    assert result.data['environmentSchemaOrError']['__typename'] == 'EnvironmentSchema'
    assert (
        result.data['environmentSchemaOrError']['configTypeOrError']['__typename']
        == 'ConfigTypeNotFoundError'
    )

    snapshot.assert_match(result.data)


ENVIRONMENT_SCHEMA_CONFIG_VALIDATION_QUERY = '''
query PipelineQuery(
    $environmentConfigData: EnvironmentConfigData,
    $selector: ExecutionSelector!,
    $mode: String!
) {
  environmentSchemaOrError(selector: $selector mode: $mode) {
    ... on EnvironmentSchema {
      isEnvironmentConfigValid(environmentConfigData: $environmentConfigData) {
        __typename
        ... on PipelineConfigValidationValid {
            pipeline { name }
        }
        ... on PipelineConfigValidationInvalid {
            pipeline { name }
            errors {
                __typename
                ... on RuntimeMismatchConfigError {
                    type { name }
                    valueRep
                }
                ... on MissingFieldConfigError {
                    field { name }
                }
                ... on MissingFieldsConfigError {
                    fields { name }
                }
                ... on FieldNotDefinedConfigError {
                    fieldName
                }
                ... on FieldsNotDefinedConfigError {
                    fieldNames
                }
                ... on SelectorTypeConfigError {
                    incomingFields
                }
                message
                reason
                stack {
                    entries {
                        __typename
                        ... on EvaluationStackPathEntry {
                            field {
                                name
                                configType {
                                    name
                                }
                            }
                        }
                        ... on EvaluationStackListItemEntry {
                            listIndex
                        }
                    }
                }
            }
        }
        ... on PipelineNotFoundError {
            pipelineName
        }
      }
    }
  }
}
'''


def test_basic_valid_config_on_environment_schema(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_CONFIG_VALIDATION_QUERY,
        variables={
            'selector': {'name': 'csv_hello_world'},
            'mode': 'default',
            'environmentConfigData': csv_hello_world_solids_config(),
        },
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['environmentSchemaOrError']['isEnvironmentConfigValid']['__typename']
        == 'PipelineConfigValidationValid'
    )
    snapshot.assert_match(result.data)


def test_basic_invalid_config_on_environment_schema(snapshot):
    result = execute_dagster_graphql(
        define_context(),
        ENVIRONMENT_SCHEMA_CONFIG_VALIDATION_QUERY,
        variables={
            'selector': {'name': 'csv_hello_world'},
            'mode': 'default',
            'environmentConfigData': {'nope': 'kdjfd'},
        },
    )

    assert not result.errors
    assert result.data
    assert (
        result.data['environmentSchemaOrError']['isEnvironmentConfigValid']['__typename']
        == 'PipelineConfigValidationInvalid'
    )
    snapshot.assert_match(result.data)
