import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { ApolloClient, ApolloQueryResult } from "apollo-boost";
import { Query, QueryResult } from "react-apollo";
import ConfigCodeEditor from "./ConfigCodeEditor";
import { ValidationResult } from "./codemirror-yaml/mode";
import { ConfigCodeEditorContainerQuery } from "./types/ConfigCodeEditorContainerQuery";
import { ConfigCodeEditorContainerCheckConfigQuery } from "./types/ConfigCodeEditorContainerCheckConfigQuery";

interface IConfigCodeEditorContainerProps {
  pipelineName: string;
  environmentTypeName: string;
  configCode: string;
  onConfigChange: (newValue: string) => void;
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
                    checkConfig={json =>
                      checkConfig(
                        queryResult.client,
                        this.props.pipelineName,
                        json
                      )
                    }
                    configCode={this.props.configCode}
                    onConfigChange={this.props.onConfigChange}
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

export const CONFIG_CODE_EDITOR_CONTAINER_CHECK_CONFIG_QUERY = gql`
  query ConfigCodeEditorContainerCheckConfigQuery(
    $pipelineName: String!
    $config: GenericScalar!
  ) {
    isPipelineConfigValid(pipelineName: $pipelineName, config: $config) {
      __typename

      ... on PipelineConfigValidationInvalid {
        errors {
          message
          path
        }
      }
    }
  }
`;

async function checkConfig(
  client: ApolloClient<any>,
  pipelineName: string,
  config: any
): Promise<ValidationResult> {
  if (config !== null) {
    const result = await client.query<
      ConfigCodeEditorContainerCheckConfigQuery
    >({
      query: CONFIG_CODE_EDITOR_CONTAINER_CHECK_CONFIG_QUERY,
      variables: {
        pipelineName,
        config
      },
      fetchPolicy: "no-cache"
    });

    if (
      result.data.isPipelineConfigValid.__typename ===
      "PipelineConfigValidationInvalid"
    ) {
      return {
        isValid: false,
        errors: result.data.isPipelineConfigValid.errors
      };
    }
  }
  return {
    isValid: true
  };
}
