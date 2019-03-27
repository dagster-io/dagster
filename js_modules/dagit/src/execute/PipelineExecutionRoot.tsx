import * as React from "react";
import gql from "graphql-tag";
import { match } from "react-router";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { StorageProvider } from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";
import Loading from "../Loading";

interface IPipelineExecutionRootProps {
  match: match<{ pipelineName: string }>;
}

export default class PipelineExecutionRoot extends React.Component<
  IPipelineExecutionRootProps
> {
  render() {
    const { pipelineName } = this.props.match.params;

    return (
      <StorageProvider namespace={pipelineName} key={pipelineName}>
        {({ data, onSave }) => (
          <Query
            query={PIPELINE_EXECUTION_ROOT_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
            variables={{
              name: pipelineName,
              solidSubset: data.sessions[data.current].solidSubset
            }}
          >
            {(queryResult: QueryResult<PipelineExecutionRootQuery, any>) => (
              <Loading queryResult={queryResult}>
                {result => (
                  <PipelineExecutionContainer
                    data={data}
                    onSave={onSave}
                    pipeline={result.pipeline}
                    currentSession={data.sessions[data.current]}
                  />
                )}
              </Loading>
            )}
          </Query>
        )}
      </StorageProvider>
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
