import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { Query, QueryResult } from "react-apollo";
import ConfigCodeEditor from "./ConfigCodeEditor";
import { ConfigCodeEditorContainerQuery } from "./types/ConfigCodeEditorContainerQuery";

interface IConfigCodeEditorContainerProps {
  pipelineName: string;
  environmentTypeName: string;
}

export default class ConfigCodeEditorContainer extends React.Component<
  IConfigCodeEditorContainerProps,
  {}
> {
  render() {
    return (
      <Query
        query={CONFIG_CODE_EDITOR_CONTAINER_QUERY}
        variables={{
          pipelineName: this.props.pipelineName
        }}
      >
        {(
          queryResult: QueryResult<
            ConfigCodeEditorContainerQuery,
            { pipelineName: string }
          >
        ) => {
          return (
            <Loading queryResult={queryResult}>
              {data => {
                const typeConfig = createTypeConfig(
                  data,
                  this.props.environmentTypeName
                );
                return (
                  <ConfigCodeEditor
                    typeConfig={typeConfig}
                    lintJson={async () => ({
                      valid: false,
                      errors: [
                        {
                          message: "There is an error",
                          path: ["context", "production"]
                        }
                      ]
                    })}
                  />
                );
              }}
            </Loading>
          );
        }}
      </Query>
    );
  }
}

export const CONFIG_CODE_EDITOR_CONTAINER_QUERY = gql`
  query ConfigCodeEditorContainerQuery($pipelineName: String!) {
    types(pipelineName: $pipelineName) {
      __typename
      name
      ... on CompositeType {
        fields {
          name
          type {
            name
          }
        }
      }
    }
  }
`;

function createTypeConfig(
  types: ConfigCodeEditorContainerQuery,
  environmentTypeName: string
): {
  environment: Array<{ name: string; typeName: string }>;
  types: {
    [name: string]: Array<{
      name: string;
      typeName: string;
    }>;
  };
} {
  const typeMap = {};
  for (const type of types.types) {
    if (type.__typename === "CompositeType") {
      typeMap[type.name] = type.fields.map(({ name, type }) => ({
        name,
        typeName: type.name
      }));
    }
  }
  return {
    environment: typeMap[environmentTypeName] || [],
    types: typeMap
  };
}
