import {gql} from '@apollo/client';

import {YamlModeValidationResult} from 'src/configeditor/codemirror-yaml/mode';
import {ConfigEditorValidationFragment} from 'src/configeditor/types/ConfigEditorValidationFragment';

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
    ... on PipelineConfigValidationInvalid {
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
          }
        }
      }
    }
  }
`;

export type StackEntry =
  | {
      __typename: 'EvaluationStackPathEntry';
      fieldName: string;
    }
  | {
      __typename: 'EvaluationStackListItemEntry';
      listIndex: number;
    };

export function errorStackToYamlPath(entries: StackEntry[]) {
  return entries.map((entry) =>
    entry.__typename === 'EvaluationStackPathEntry' ? entry.fieldName : `${entry.listIndex}`,
  );
}

export function responseToYamlValidationResult(
  configJSON: object,
  response: ConfigEditorValidationFragment,
): YamlModeValidationResult {
  if (response.__typename !== 'PipelineConfigValidationInvalid') {
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
  const topLevelKey = Object.keys(configJSON);
  errors.forEach((error) => {
    if (error.path.length === 0 && topLevelKey.length) {
      error.path = [topLevelKey[0]];
    }
  });

  return {isValid: false, errors};
}
