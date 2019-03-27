import * as React from "react";
import gql from "graphql-tag";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { PipelineRunRootQuery } from "./types/PipelineRunRootQuery";
import { PipelineRun } from "./PipelineRun";
import Loading from "../Loading";
import RunSubscriptionProvider from "./RunSubscriptionProvider";

interface IPipelineRunRootProps {
  pipeline: string;
  runId: string;
}

export default class PipelineRunRoot extends React.Component<
  IPipelineRunRootProps
> {
  render() {
    return (
      <ApolloConsumer>
        {client => (
          <Query
            query={PIPELINE_RUN_ROOT_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
            variables={{ runId: this.props.runId }}
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
