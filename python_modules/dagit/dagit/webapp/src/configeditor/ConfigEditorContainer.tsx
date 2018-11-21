import * as React from "react";
import gql from "graphql-tag";
import Loading from "../Loading";
import { ApolloClient, ApolloQueryResult } from "apollo-boost";
import { Query, QueryResult } from "react-apollo";
import ConfigEditor from "./ConfigEditor";
import { ValidationResult, TypeConfig } from "./codemirror-yaml/mode";
import { ConfigEditorContainerQuery } from "./types/ConfigEditorContainerQuery";
import { ConfigEditorContainerCheckConfigQuery } from "./types/ConfigEditorContainerCheckConfigQuery";

interface IConfigEditorContainerProps {
  pipelineName: string;
  environmentTypeName: string;
  availableConfigs: Array<string>;
  selectedConfig: string | null;
  configCode: string | null;
  onCreateConfig: (newConfig: string) => void;
  onChangeConfig: (newValue: string) => void;
  onSelectConfig: (newConfig: string | null) => void;
  onDeleteConfig: (configName: string) => void;
}

export default class ConfigEditorContainer extends React.Component<
  IConfigEditorContainerProps,
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
            ConfigEditorContainerQuery,
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
                  <ConfigEditor
                    typeConfig={typeConfig}
                    configCode={this.props.configCode}
                    availableConfigs={this.props.availableConfigs}
                    selectedConfig={this.props.selectedConfig}
                    onCreateConfig={this.props.onCreateConfig}
                    onSelectConfig={this.props.onSelectConfig}
                    onChangeConfig={this.props.onChangeConfig}
                    onDeleteConfig={this.props.onDeleteConfig}
                    onCheckConfig={json =>
                      checkConfig(
                        queryResult.client,
                        this.props.pipelineName,
                        json
                      )
                    }
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
  query ConfigEditorContainerQuery($pipelineName: String!) {
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
  types: ConfigEditorContainerQuery,
  environmentTypeName: string
): TypeConfig {
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
  query ConfigEditorContainerCheckConfigQuery(
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
    const result = await client.query<ConfigEditorContainerCheckConfigQuery>({
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
