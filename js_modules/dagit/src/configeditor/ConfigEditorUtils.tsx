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
      isSelector
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
    $pipeline: ExecutionSelector!
    $config: PipelineConfig!
  ) {
    isPipelineConfigValid(pipeline: $pipeline, config: $config) {
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
  }
`;

interface ITypeConfig {
  rootTypeName: string;
  types: {
    [name: string]: {
      isSelector: boolean;
      fields: Array<{
        name: string;
        isOptional: boolean;
        type: {
          name: string;
        };
      }>;
    };
  };
}

export function createTypeConfig({
  types,
  environmentType
}: ConfigEditorPipelineFragment): ITypeConfig {
  const result: ITypeConfig = {
    types: {},
    rootTypeName: environmentType.name
  };

  for (const type of types) {
    if (type.__typename === "CompositeType") {
      result.types[type.name] = type;
    }
  }

  return result;
}

export async function checkConfig(
  client: ApolloClient<any>,
  config: any,
  pipeline: { name: string; solidSubset: string[] | null }
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
    variables: { pipeline, config },
    fetchPolicy: "no-cache"
  });

  if (isPipelineConfigValid.__typename !== "PipelineConfigValidationInvalid") {
    return { isValid: true };
  }

  const errors = isPipelineConfigValid.errors.map(
    ({ message, reason, stack }) => ({
      message: message,
      reason: reason,
      path: stack.entries.map(
        entry =>
          entry.__typename === "EvaluationStackPathEntry"
            ? entry.field.name
            : `${entry.listIndex}`
      )
    })
  );

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
    Int: 1,
    Boolean: "false"
  };

  const configPlaceholderFor = (
    typeName: string,
    commentDepth: number
  ): any => {
    if (placeholders[typeName]) {
      return placeholders[typeName];
    }

    const type = types[typeName];
    if (!type) return null;

    const result = {};
    type.fields.filter(f => !f.isOptional).forEach((field, idx) => {
      const startComment = type.isSelector && idx > 0;
      const fieldCommentDepth =
        commentDepth > 0 ? commentDepth + 2 : startComment ? 1 : 0;

      const val = configPlaceholderFor(field.type.name, fieldCommentDepth);
      if (!val || Object.keys(val).length == 0) return;

      if (fieldCommentDepth > 0) {
        result[`COMMENTED_${fieldCommentDepth}_${field.name}`] = val;
      } else {
        result[field.name] = val;
      }
    });
    return result;
  };

  // Convert the top level to a YAML string
  let obj = configPlaceholderFor(pipeline.environmentType.name, 0);
  let str = YAML.stringify(obj);

  // Comment lines containing the COMMENTED_X_ prefix. X indicates how
  // much of the preceding indentation should be placed after the #,
  // allowing us to match the Codemirror comment strategy where entire
  // blocks are commented with a vertically aligned row of # characters.
  str = str.replace(/\n([\s]+)COMMENTED_(\d+)_/g, (_, whitespace, depth) => {
    const preWhitespace = whitespace.substr(0, whitespace.length - depth / 1);
    const postWhitespace = Array(depth / 1)
      .fill(" ")
      .join("");
    return `\n${preWhitespace} #${postWhitespace}`;
  });

  // It's unclear why YAML.stringify returns an empty object when the provided
  // input is empty, but we'd rather just display nothing in the editor.
  if (str === "{}\n") {
    str = "";
  }

  return `
# This config has been auto-generated with required fields.
# Additional optional settings may be available.

${str}
`;
}
