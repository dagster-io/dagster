import {gql} from '@apollo/client';
import {YamlModeValidationResult} from '@dagster-io/ui';
import yaml from 'yaml';

import {ConfigEditorValidationFragment} from './types/ConfigEditorValidationFragment';

export const CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT = gql`
  fragment ConfigEditorRunConfigSchemaFragment on RunConfigSchema {
    rootConfigType {
      key
    }
    allConfigTypes {
      __typename
      key
      description
      isSelector
      typeParamKeys
      ... on RegularConfigType {
        givenName
      }
      ... on MapConfigType {
        keyLabelName
      }
      ... on EnumConfigType {
        givenName
        values {
          value
          description
        }
      }
      ... on CompositeConfigType {
        fields {
          name
          description
          isRequired
          configTypeKey
          defaultValueAsJson
        }
      }
      ... on ScalarUnionConfigType {
        key
        scalarTypeKey
        nonScalarTypeKey
      }
    }
  }
`;

export const CONFIG_EDITOR_VALIDATION_FRAGMENT = gql`
  fragment ConfigEditorValidationFragment on PipelineConfigValidationResult {
    __typename
    ... on RunConfigValidationInvalid {
      errors {
        __typename
        reason
        message
        stack {
          entries {
            __typename
            ... on EvaluationStackPathEntry {
              fieldName
            }
            ... on EvaluationStackListItemEntry {
              listIndex
            }
            ... on EvaluationStackMapKeyEntry {
              mapKey
            }
            ... on EvaluationStackMapValueEntry {
              mapKey
            }
          }
        }
      }
    }
  }
`;

type StackEntry =
  | {
      __typename: 'EvaluationStackPathEntry';
      fieldName: string;
    }
  | {
      __typename: 'EvaluationStackListItemEntry';
      listIndex: number;
    }
  | {
      __typename: 'EvaluationStackMapKeyEntry';
      mapKey: object;
    }
  | {
      __typename: 'EvaluationStackMapValueEntry';
      mapKey: object;
    };

export function errorStackToYamlPath(entries: StackEntry[]) {
  return entries.map((entry) => {
    switch (entry.__typename) {
      case 'EvaluationStackPathEntry':
        return entry.fieldName;
      case 'EvaluationStackListItemEntry':
        return `${entry.listIndex}`;
      case 'EvaluationStackMapKeyEntry':
      case 'EvaluationStackMapValueEntry':
        return `${entry.mapKey}`;
    }
  });
}

export function responseToYamlValidationResult(
  configYaml: string,
  response: ConfigEditorValidationFragment,
): YamlModeValidationResult {
  if (response.__typename !== 'RunConfigValidationInvalid') {
    return {isValid: true};
  }

  const errors = response.errors.map((err) => ({
    message: err.message,
    reason: err.reason,
    path: errorStackToYamlPath(err.stack.entries),
  }));

  // Errors at the top level have no stack path because they are not within any
  // dicts. To avoid highlighting the entire editor, associate them with the first
  // element of the top dict.
  const parsed = yaml.parse(configYaml);
  const topLevelKey = Object.keys(parsed);
  errors.forEach((error) => {
    if (error.path.length === 0 && topLevelKey.length) {
      error.path = [topLevelKey[0]];
    }
  });

  return {isValid: false, errors};
}
