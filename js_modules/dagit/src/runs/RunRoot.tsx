import * as React from "react";
import { match, Redirect } from "react-router";
import gql from "graphql-tag";
import { useApolloClient, useQuery } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { Run } from "./Run";
import { RunRootQuery } from "./types/RunRootQuery";

interface IRunRootProps {
  match: match<{ runId: string; pipelineName?: string }>;
}

export const RunRoot: React.FunctionComponent<IRunRootProps> = props => {
  const { pipelineName, runId } = props.match.params;
  const client = useApolloClient();
  const { data } = useQuery<RunRootQuery>(RUN_ROOT_QUERY, {
    fetchPolicy: "cache-and-network",
    partialRefetch: true,
    variables: { runId }
  });

  if (!data || !data.pipelineRunOrError) {
    return <Run client={client} run={undefined} />;
  }

  if (data.pipelineRunOrError.__typename !== "PipelineRun") {
    return (
      <NonIdealState
        icon={IconNames.SEND_TO_GRAPH}
        title="No Run"
        description={
          "The run with this ID does not exist or has been cleaned up."
        }
      />
    );
  }

  if (!pipelineName || pipelineName !== data.pipelineRunOrError.pipeline.name) {
    // legacy support for the /runs/:runId endpoint
    return (
      <Redirect
        to={{
          pathname: `/p/${data.pipelineRunOrError.pipeline.name}/runs/${runId}`
        }}
      />
    );
  }

  return <Run client={client} run={data.pipelineRunOrError} />;
};

export const RUN_ROOT_QUERY = gql`
  query RunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PipelineRun {
        pipeline {
          name
        }
        ...RunFragment
      }
    }
  }

  ${Run.fragments.RunFragment}
`;
