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
            variables={{
              runId: this.props.runId
            }}
          >
            {(queryResult: QueryResult<PipelineRunRootQuery, any>) => (
              <Loading queryResult={queryResult}>
                {({ pipelineRun }) =>
                  pipelineRun ? (
                    <>
                      <RunSubscriptionProvider
                        client={client}
                        runLogCursor={pipelineRun.logs.pageInfo.lastCursor}
                        runId={pipelineRun.runId}
                      />
                      <PipelineRun run={pipelineRun} />
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
    pipelineRun(runId: $runId) {
      runId
      logs {
        pageInfo {
          lastCursor
        }
      }
      ...PipelineRunFragment
    }
  }

  ${PipelineRun.fragments.PipelineRunFragment}
`;
