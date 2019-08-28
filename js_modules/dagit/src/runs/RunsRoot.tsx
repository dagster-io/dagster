import * as React from "react";
import gql from "graphql-tag";
import RunHistory from "./RunHistory";
import { QueryResult, Query } from "react-apollo";
import { RunsRootQuery } from "./types/RunsRootQuery";
import Loading from "../Loading";

export default class RunsRoot extends React.Component {
  render() {
    return (
      <Query
        query={RUNS_ROOT_QUERY}
        fetchPolicy="cache-and-network"
        pollInterval={15 * 1000}
        partialRefetch={true}
      >
        {(queryResult: QueryResult<RunsRootQuery, any>) => (
          <Loading queryResult={queryResult}>
            {result => <RunHistory runs={result.pipelineRuns} />}
          </Loading>
        )}
      </Query>
    );
  }
}

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery {
    pipelineRuns {
      ...RunHistoryRunFragment
    }
  }

  ${RunHistory.fragments.RunHistoryRunFragment}
`;
