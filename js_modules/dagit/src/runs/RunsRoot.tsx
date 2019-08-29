import * as React from "react";
import gql from "graphql-tag";
import RunHistory from "./RunHistory";
import { useQuery } from "react-apollo";
import { RunsRootQuery } from "./types/RunsRootQuery";
import Loading from "../Loading";

export const RunsRoot: React.FunctionComponent = () => {
  const queryResult = useQuery<RunsRootQuery>(RUNS_ROOT_QUERY, {
    fetchPolicy: "cache-and-network",
    pollInterval: 15 * 1000,
    partialRefetch: true
  });
  return (
    <Loading queryResult={queryResult}>
      {result => <RunHistory runs={result.pipelineRuns} />}
    </Loading>
  );
};

export const RUNS_ROOT_QUERY = gql`
  query RunsRootQuery {
    pipelineRuns {
      ...RunHistoryRunFragment
    }
  }

  ${RunHistory.fragments.RunHistoryRunFragment}
`;
