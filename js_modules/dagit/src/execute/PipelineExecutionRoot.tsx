import * as React from "react";
import gql from "graphql-tag";
import { match } from "react-router";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { useStorage } from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";

interface IPipelineExecutionRootProps {
  match: match<{ pipelineName: string }>;
}

export const PipelineExecutionRoot: React.FunctionComponent<
  IPipelineExecutionRootProps
> = ({ match: { params } }) => {
  const [data, onSave] = useStorage({ namespace: params.pipelineName });
  const vars = {
    name: params.pipelineName,
    solidSubset: data.sessions[data.current].solidSubset,
    mode: data.sessions[data.current].mode
  };

  return (
    <Query
      // never serve cached Pipeline given new vars by forcing teardown of the Query.
      // Apollo's behaviors are sort of whacky, even with no-cache. Should just use
      // window.fetch...
      key={JSON.stringify(vars)}
      query={PIPELINE_EXECUTION_ROOT_QUERY}
      fetchPolicy="cache-and-network"
      partialRefetch={true}
      variables={vars}
    >
      {(result: QueryResult<PipelineExecutionRootQuery, any>) => {
        const pipelineOrError = result.data && result.data.pipelineOrError;
        const environmentSchemaOrError =
          result.data && result.data.environmentSchemaOrError;

        if (
          (environmentSchemaOrError &&
            environmentSchemaOrError.__typename === "PipelineNotFoundError") ||
          (pipelineOrError &&
            pipelineOrError.__typename === "PipelineNotFoundError")
        ) {
          const message =
            pipelineOrError &&
            pipelineOrError.__typename === "PipelineNotFoundError"
              ? pipelineOrError.message
              : "No data returned from GraphQL";

          return (
            <NonIdealState
              icon={IconNames.FLOW_BRANCH}
              title="Pipeline Not Found"
              description={message}
            />
          );
        }

        if (pipelineOrError && pipelineOrError.__typename === "PythonError") {
          return (
            <NonIdealState
              icon={IconNames.ERROR}
              title="Python Error"
              description={pipelineOrError.message}
            />
          );
        }

        return (
          <PipelineExecutionContainer
            data={data}
            onSave={onSave}
            pipelineOrError={pipelineOrError}
            environmentSchemaOrError={environmentSchemaOrError}
            pipelineName={params.pipelineName}
            currentSession={data.sessions[data.current]}
          />
        );
      }}
    </Query>
  );
};

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query PipelineExecutionRootQuery(
    $name: String!
    $solidSubset: [String!]
    $mode: String
  ) {
    pipelineOrError(params: { name: $name, solidSubset: $solidSubset }) {
      ... on PipelineNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
      ...PipelineExecutionContainerFragment
    }
    environmentSchemaOrError(
      selector: { name: $name, solidSubset: $solidSubset }
      mode: $mode
    ) {
      ...PipelineExecutionContainerEnvironmentSchemaFragment
    }
  }

  ${PipelineExecutionContainer.fragments.PipelineExecutionContainerFragment}
  ${PipelineExecutionContainer.fragments.EnvironmentSchemaOrErrorFragment}
`;
