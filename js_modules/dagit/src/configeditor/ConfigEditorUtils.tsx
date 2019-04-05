import gql from "graphql-tag";
import { ValidationResult } from "./codemirror-yaml/mode";
import { ConfigEditorValidationFragment } from "./types/ConfigEditorValidationFragment";

export const CONFIG_EDITOR_PIPELINE_FRAGMENT = gql`
  fragment ConfigEditorPipelineFragment on Pipeline {
    name
    environmentType {
      key
    }
    configTypes {
      __typename
      key
      name
      isSelector
      ... on EnumConfigType {
        values {
          value
          description
        }
      }
      ... on CompositeConfigType {
        fields {
          name
          isOptional
          configType {
            __typename
            key
            name
            isList
            isNullable
            ... on ListConfigType {
              innerTypes {
                __typename
                key
                ... on ListConfigType {
                  ofType {
                    __typename
                    key
                  }
                }
              }
              ofType {
                __typename
                key
              }
            }
          }
        }
      }
    }
  }
`;

export const CONFIG_EDITOR_VALIDATION_FRAGMENT = gql`
  fragment ConfigEditorValidationFragment on PipelineConfigValidationResult {
    __typename
    ... on PipelineConfigValidationInvalid {
      errors {
        reason
        message
        stack {
          entries {
            __typename
            ... on EvaluationStackPathEntry {
              field {
                name
              }
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

export async function responseToValidationResult(
  config: object,
  response: ConfigEditorValidationFragment
): Promise<ValidationResult> {
  if (response.__typename !== "PipelineConfigValidationInvalid") {
    return { isValid: true };
  }

  const errors = response.errors.map(({ message, reason, stack }) => ({
    message: message,
    reason: reason,
    path: stack.entries.map(entry =>
      entry.__typename === "EvaluationStackPathEntry"
        ? entry.field.name
        : `${entry.listIndex}`
    )
  }));

  // Errors at the top level have no stack path because they are not within any
  // dicts. To avoid highlighting the entire editor, associate them with the first
  // element of the top dict.
  const topLevelKey = Object.keys(config);
  errors.forEach(error => {
    if (error.path.length === 0 && topLevelKey.length) {
      error.path = [topLevelKey[0]];
    }
  });

  return { isValid: false, errors: errors };
}
