import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { PipelineRunRootQuery } from "./types/PipelineRunRootQuery";
import { PipelineStatusToPageAttributes } from "./PipelineStatusToPageAttributes";
import { PipelineRun } from "./PipelineRun";
import Loading from "../Loading";
import RunSubscriptionProvider from "./RunSubscriptionProvider";

interface IPipelineRunRootProps {
  match: match<{ pipelineName: string; runId: string }>;
}

export default class PipelineRunRoot extends React.Component<
  IPipelineRunRootProps
> {
  render() {
    const { runId, pipelineName } = this.props.match.params;

    return (
      <ApolloConsumer>
        {client => (
          <Query
            query={PIPELINE_RUN_ROOT_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
            variables={{ runId }}
          >
            {(queryResult: QueryResult<PipelineRunRootQuery, any>) => (
              <Loading queryResult={queryResult}>
                {({ pipelineRunOrError }) =>
                  pipelineRunOrError.__typename === "PipelineRun" ? (
                    <>
                      <RunSubscriptionProvider
                        client={client}
                        runId={pipelineRunOrError.runId}
                        runLogCursor={
                          pipelineRunOrError.logs.pageInfo.lastCursor
                        }
                      />
                      <PipelineStatusToPageAttributes
                        pipelineName={pipelineName}
                        runId={pipelineRunOrError.runId}
                        status={pipelineRunOrError.status}
                      />
                      <PipelineRun run={pipelineRunOrError} />
                    </>
                  ) : (
                    <NonIdealState
                      icon={IconNames.SEND_TO_GRAPH}
                      title="No Run"
                      description={
                        "The run with this ID does not exist or has been cleaned up."
                      }
                    />
                  )
                }
              </Loading>
            )}
          </Query>
        )}
      </ApolloConsumer>
    );
  }
}

export const PIPELINE_RUN_ROOT_QUERY = gql`
  query PipelineRunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PipelineRun {
        runId
        status
        logs {
          pageInfo {
            lastCursor
          }
        }
        ...PipelineRunFragment
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunFragment}
`;
