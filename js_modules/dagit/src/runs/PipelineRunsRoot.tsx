import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import RunHistory from "./RunHistory";
import { QueryResult, Query } from "react-apollo";
import { PipelineRunsRootQuery } from "./types/PipelineRunsRootQuery";
import Loading from "../Loading";

interface IPipelineExecutionRootProps {
  match: match<{ pipelineName: string }>;
}

export default class PipelineRunsRoot extends React.Component<
  IPipelineExecutionRootProps
> {
  render() {
    const { pipelineName } = this.props.match.params;

    return (
      <Query
        query={PIPELINE_RUNS_ROOT_QUERY}
        fetchPolicy="cache-and-network"
        partialRefetch={true}
        variables={{ name: pipelineName }}
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
