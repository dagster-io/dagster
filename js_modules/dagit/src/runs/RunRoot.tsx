import * as React from "react";
import { match } from "react-router";
import gql from "graphql-tag";
import { QueryResult, Query, ApolloConsumer } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { RunRootQuery } from "./types/RunRootQuery";
import { Run } from "./Run";

interface IRunRootProps {
  match: match<{ runId: string }>;
}

export default class RunRoot extends React.Component<IRunRootProps> {
  render() {
    const { runId } = this.props.match.params;
    return (
      <ApolloConsumer>
        {client => (
          <Query
            query={RUN_ROOT_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
            variables={{ runId }}
          >
            {({ data }: QueryResult<RunRootQuery, any>) =>
              !data || !data.pipelineRunOrError ? (
                <Run client={client} run={undefined} />
              ) : data.pipelineRunOrError.__typename === "PipelineRun" ? (
                <Run client={client} run={data.pipelineRunOrError} />
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

export const RUN_ROOT_QUERY = gql`
  query RunRootQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      __typename
      ... on PipelineRun {
        ...RunFragment
      }
    }
  }

  ${Run.fragments.RunFragment}
`;
