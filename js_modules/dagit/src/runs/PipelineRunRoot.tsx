import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { PipelineRunRootQuery } from "./types/PipelineRunRootQuery";
import { PipelineRun } from "./PipelineRun";

interface IPipelineRunRootProps {
  match: match<{ pipelineName: string; runId: string }>;
}

export default class PipelineRunRoot extends React.Component<
  IPipelineRunRootProps
> {
  render() {
    const { runId } = this.props.match.params;

    return (
      <ApolloConsumer>
        {client => (
          <Query
            query={PIPELINE_RUN_ROOT_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
            variables={{ runId }}
          >
            {({ data }: QueryResult<PipelineRunRootQuery, any>) =>
              !data || !data.pipelineRunOrError ? (
                <PipelineRun client={client} run={undefined} />
              ) : data.pipelineRunOrError.__typename === "PipelineRun" ? (
                <PipelineRun client={client} run={data.pipelineRunOrError} />
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
        ...PipelineRunFragment
      }
    }
  }

  ${PipelineRun.fragments.PipelineRunFragment}
`;
