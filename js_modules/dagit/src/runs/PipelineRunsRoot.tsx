import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import RunHistory from "./RunHistory";
import { QueryResult, Query } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
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
            {result => {
              const pipelineOrError = result.pipelineOrError;

              switch (pipelineOrError.__typename) {
                case "PipelineNotFoundError":
                  return (
                    <NonIdealState
                      icon={IconNames.FLOW_BRANCH}
                      title="Pipeline Not Found"
                      description={pipelineOrError.message}
                    />
                  );
                case "Pipeline":
                  return (
                    <RunHistory
                      pipelineName={pipelineOrError.name}
                      runs={pipelineOrError.runs}
                    />
                  );
                default:
                  return null;
              }
            }}
          </Loading>
        )}
      </Query>
    );
  }
}

export const PIPELINE_RUNS_ROOT_QUERY = gql`
  query PipelineRunsRootQuery($name: String!) {
    pipelineOrError(params: { name: $name }) {
      ... on Pipeline {
        name
        runs {
          ...RunHistoryRunFragment
        }
      }
      ... on PipelineNotFoundError {
        message
      }
    }
  }

  ${RunHistory.fragments.RunHistoryRunFragment}
`;
