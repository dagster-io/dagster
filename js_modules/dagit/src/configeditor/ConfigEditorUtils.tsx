import gql from "graphql-tag";
import { ApolloClient } from "apollo-boost";
import { ValidationResult } from "./codemirror-yaml/mode";
import { ConfigEditorPipelineFragment } from "./types/ConfigEditorPipelineFragment";
import {
  ConfigEditorCheckConfigQuery,
  ConfigEditorCheckConfigQueryVariables
} from "./types/ConfigEditorCheckConfigQuery";
import * as YAML from "yaml";

export const CONFIG_EDITOR_PIPELINE_FRAGMENT = gql`
  fragment ConfigEditorPipelineFragment on Pipeline {
    name
    environmentType {
      name
    }
    types {
      __typename
      name
      ... on CompositeType {
        fields {
          name
          isOptional
          type {
            name
          }
        }
      }
    }
  }
`;

export const CONFIG_EDITOR_CHECK_CONFIG_QUERY = gql`
  query ConfigEditorCheckConfigQuery(
    $executionParams: PipelineExecutionParams!
  ) {
    isPipelineConfigValid(executionParams: $executionParams) {
      __typename

      ... on PipelineConfigValidationInvalid {
        errors {
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
  }
`;

interface ITypeConfig {
  environment: Array<{ name: string; typeName: string }>;
  types: {
    [name: string]: Array<{
      name: string;
      typeName: string;
      isOptional: boolean;
    }>;
  };
}

export function createTypeConfig({
  types,
  environmentType
}: ConfigEditorPipelineFragment): ITypeConfig {
  const typeMap = {};
  for (const type of types) {
    if (type.__typename === "CompositeType") {
      typeMap[type.name] = type.fields.map(({ name, type, isOptional }) => ({
        name,
        typeName: type.name,
        isOptional
      }));
    }
  }
  return {
    environment: typeMap[environmentType.name] || [],
    types: typeMap
  };
}

export async function checkConfig(
  client: ApolloClient<any>,
  pipelineName: string,
  config: any
): Promise<ValidationResult> {
  if (config === null) {
    return { isValid: true };
  }
  const {
    data: { isPipelineConfigValid }
  } = await client.query<
    ConfigEditorCheckConfigQuery,
    ConfigEditorCheckConfigQueryVariables
  >({
    query: CONFIG_EDITOR_CHECK_CONFIG_QUERY,
    variables: {
      executionParams: {
        pipelineName: pipelineName,
        config: config
      }
    },
    fetchPolicy: "no-cache"
  });

  if (isPipelineConfigValid.__typename !== "PipelineConfigValidationInvalid") {
    return { isValid: true };
  }

  const errors = isPipelineConfigValid.errors.map(({ message, stack }) => ({
    message: message,
    path: stack.entries.map(
      entry =>
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

export function scaffoldConfig(pipeline: ConfigEditorPipelineFragment): string {
  const { types } = createTypeConfig(pipeline);

  const placeholders = {
    Path: "/path/to/file",
    String: "value",
    Int: `0`,
    Boolean: `false`
  };

  const configPlaceholderFor = (typeName: string): any => {
    if (placeholders[typeName]) {
      return placeholders[typeName];
    }

    const type = types[typeName];
    if (!type) return null;

    const result = {};
    for (const field of type) {
      if (field.isOptional) continue;
      const val = configPlaceholderFor(field.typeName);
      if (Object.keys(val).length > 0) {
        result[field.name] = val;
      }
    }
    return result;
  };

  return `
# This config has been auto-generated with required fields.
# Additional optional settings may be available.

${YAML.stringify(configPlaceholderFor(pipeline.environmentType.name))}
`;
}
