import gql from "graphql-tag";
import { ApolloClient } from "apollo-boost";
import { ValidationResult } from "./codemirror-yaml/mode";
import {
  ConfigEditorPipelineFragment,
  ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes
} from "./types/ConfigEditorPipelineFragment";
import {
  ConfigEditorCheckConfigQuery,
  ConfigEditorCheckConfigQueryVariables
} from "./types/ConfigEditorCheckConfigQuery";
import * as YAML from "yaml";

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
          description
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
      path: stack.entries.map(entry =>
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

function nullOrEmpty(val: any) {
  return (
    val === null || (val instanceof Object && Object.keys(val).length == 0)
  );
}

export function scaffoldConfig(pipeline: ConfigEditorPipelineFragment): string {
  const placeholders = {
    Path: "/path/to/file",
    String: "value",
    Int: 1,
    Bool: false,
    Float: 1.0
  };

  const configPlaceholderFor = (typeKey: string, commentDepth: number): any => {
    if (placeholders[typeKey] !== undefined) {
      return placeholders[typeKey];
    }

    const type = pipeline.configTypes.find(t => t.key === typeKey);
    if (!type) {
      console.warn(`Unsure of how to scaffold missing type: ${typeKey}`);
      return null;
    }

    if (type.__typename === "CompositeConfigType") {
      const result = {};
      type.fields.forEach((field, idx) => {
        const startComment = type.isSelector && idx > 0;
        const fieldCommentDepth =
          commentDepth > 0 ? commentDepth + 2 : startComment ? 1 : 0;

        let val = null;

        if (field.configType.__typename === "ListConfigType") {
          let inner: ConfigEditorPipelineFragment_configTypes_CompositeConfigType_fields_configType_ListConfigType_innerTypes =
            field.configType;
          let wrap = 0;

          // If the field's type is a list, we need to scaffold an item in the list.
          // The list could be a list of lists, though. Drill in to the `ofType` and
          // repeatedly look up the type in the top level innerTypes set until we find
          // a non-list ofType. Then we scaffold it and wrap it in layers of arrays.
          while (true) {
            if (inner.__typename !== "ListConfigType") break;
            const innerTypeKey: string = inner.ofType.key;
            inner = field.configType.innerTypes.find(
              t => t.key === innerTypeKey
            )!;
            wrap += 1;
          }
          val = configPlaceholderFor(inner.key, commentDepth);
          if (nullOrEmpty(val)) return;
          while (wrap > 0) {
            val = [val];
            wrap--;
          }
        } else {
          val = configPlaceholderFor(field.configType.key, fieldCommentDepth);
        }

        if (nullOrEmpty(val)) return;

        if (fieldCommentDepth > 0) {
          result[`COMMENTED_${fieldCommentDepth}_${field.name}`] = val;
        } else {
          result[field.name] = val;
        }
      });
      return result;
    }

    console.warn(
      `Unsure of how to scaffold ${typeKey}: ${JSON.stringify(type)}`
    );
    return null;
  };

  // Convert the top level to a YAML string
  let obj = configPlaceholderFor(pipeline.environmentType.key, 0);
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
