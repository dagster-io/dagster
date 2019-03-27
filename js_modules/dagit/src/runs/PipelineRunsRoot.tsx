import * as React from "react";
import gql from "graphql-tag";
import RunHistory from "./RunHistory";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { StorageProvider } from "../LocalStorage";
import { PipelineRunsRootQuery } from "./types/PipelineRunsRootQuery";
import Loading from "../Loading";

interface IPipelineExecutionRootProps {
  pipeline: string;
}

export default class PipelineRunsRoot extends React.Component<
  IPipelineExecutionRootProps
> {
  render() {
    return (
      <ApolloConsumer>
        {client => (
          <StorageProvider namespace={this.props.pipeline}>
            {({ data, onSave }) => (
              <Query
                query={PIPELINE_RUNS_ROOT_QUERY}
                fetchPolicy="cache-and-network"
                partialRefetch={true}
                variables={{
                  name: this.props.pipeline,
                  solidSubset: data.sessions[data.current].solidSubset
                }}
              >
                {(queryResult: QueryResult<PipelineRunsRootQuery, any>) => (
                  <Loading queryResult={queryResult}>
                    {result => (
                      <RunHistory
                        pipelineName={result.pipeline.name}
                        runs={result.pipeline.runs}
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

export const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($name: String!) {
    pipeline(params: { name: $name }) {
      name
      runs {
        ...RunHistoryRunFragment
      }
    }
  }

  ${RunHistory.fragments.RunHistoryRunFragment}
`;
