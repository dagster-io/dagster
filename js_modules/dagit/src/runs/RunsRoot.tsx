import * as React from "react";

import Loading from "../Loading";
import RunHistory from "./RunHistory";
import { RunsRootQuery } from "./types/RunsRootQuery";
import gql from "graphql-tag";
import { useQuery } from "react-apollo";

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
