import * as React from "react";
import gql from "graphql-tag";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { StorageProvider } from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";
import Loading from "../Loading";

interface IPipelineExecutionRootProps {
  pipeline: string;
}

export default class PipelineExecutionRoot extends React.Component<
  IPipelineExecutionRootProps
> {
  render() {
    return (
      <ApolloConsumer>
        {client => (
          <StorageProvider namespace={this.props.pipeline}>
            {({ data, onSave }) => (
              <Query
                query={PIPELINE_EXECUTION_ROOT_QUERY}
                fetchPolicy="cache-and-network"
                partialRefetch={true}
                variables={{
                  name: this.props.pipeline,
                  solidSubset: data.sessions[data.current].solidSubset
                }}
              >
                {(
                  queryResult: QueryResult<PipelineExecutionRootQuery, any>
                ) => (
                  <Loading queryResult={queryResult}>
                    {result => (
                      <PipelineExecutionContainer
                        data={data}
                        onSave={onSave}
                        client={client}
                        pipeline={result.pipeline}
                        currentSession={data.sessions[data.current]}
                      />
                    )}
                  </Loading>
                )}
              </Query>
            )}
          </StorageProvider>
        )}
      </ApolloConsumer>
    );
  }
}

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query PipelineExecutionRootQuery($name: String!, $solidSubset: [String!]) {
    pipeline(params: { name: $name, solidSubset: $solidSubset }) {
      name
      ...PipelineExecutionContainerFragment
    }
  }

  ${PipelineExecutionContainer.fragments.PipelineExecutionContainerFragment}
`;
