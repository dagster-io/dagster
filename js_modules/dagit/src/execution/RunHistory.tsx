import * as React from "react";
import gql from "graphql-tag";
import { Query, QueryResult } from "react-apollo";
import Loading from "../Loading";
import { RunHistoryQuery, RunHistoryQuery_pipelineRuns } from "./types/RunHistoryQuery";

interface IRunHistoryProps {
  activeRun: { runId: string } | null;
  pipelineName: string;
}

class RunHistory extends React.Component<
  IRunHistoryProps & { runs: RunHistoryQuery_pipelineRuns[] }
> {
  render() {
    return (
      <div>
        {this.props.runs.map(r => (
          <div key={r.runId}>{r.runId}</div>
        ))}
      </div>
    );
  }
}

export const RUN_HISTORY_QUERY = gql`
query RunHistoryQuery {
  pipelineRuns {
    runId
    pipeline {
      name
    }
    executionPlan {
      steps {
        name
      }
    }
  }
}
`;

export default (props: IRunHistoryProps) => (
  <Query query={RUN_HISTORY_QUERY}>
    {(queryResult: QueryResult<RunHistoryQuery, any>) => (
      <Loading queryResult={queryResult}>
        {result => <RunHistory {...props} runs={result.pipelineRuns} />}
      </Loading>
    )}
  </Query>
);
