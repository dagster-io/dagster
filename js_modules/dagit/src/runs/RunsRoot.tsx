import * as React from "react";
import gql from "graphql-tag";
import * as querystring from "query-string";
import { RouteComponentProps } from "react-router";
import RunHistory from "./RunHistory";
import { useQuery } from "react-apollo";
import { RunsRootQuery } from "./types/RunsRootQuery";
import Loading from "../Loading";

export const RunsRoot: React.FunctionComponent<RouteComponentProps> = ({
  location
}) => {
  let initialSearch = querystring.parse(location.search).q;

  const queryResult = useQuery<RunsRootQuery>(RUNS_ROOT_QUERY, {
    fetchPolicy: "cache-and-network",
    pollInterval: 15 * 1000,
    partialRefetch: true
  });

  return (
    <Loading queryResult={queryResult}>
      {result => (
        <RunHistory
          runs={result.pipelineRuns}
          initialSearch={typeof initialSearch === "string" ? initialSearch : ""}
        />
      )}
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
