import * as React from "react";
import gql from "graphql-tag";
import { match, Redirect } from "react-router";
import PipelineExecutionContainer from "./PipelineExecutionContainer";
import { QueryResult, Query } from "react-apollo";
import { NonIdealState } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  StorageProvider,
  applyCreateSession,
  IExecutionSession
} from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";
import * as querystring from "query-string";

interface IPipelineExecutionRootProps {
  match: match<{ pipelineName: string }>;
}

export const PipelineExecutionRoot: React.FunctionComponent<
  IPipelineExecutionRootProps
> = ({ match: { params } }) => (
  <StorageProvider namespace={params.pipelineName} key={params.pipelineName}>
    {({ data, onSave }) => {
      const vars = {
        name: params.pipelineName,
        solidSubset: data.sessions[data.current].solidSubset,
        mode: data.sessions[data.current].mode
      };

      // If the user has passed config via a query string, write a new session with the
      // incoming config and redirect to remove it from the URL bar.  Note: This is not
      // technically where a side effect like this should live, but placing it here
      // (before the query but after we have our StorageProvider) prevents the UI from
      // loading twice.
      const qs = querystring.parse(window.location.search);
      if (qs.config || qs.mode || qs.solidSubset) {
        const newSession: Partial<IExecutionSession> = {};
        if (typeof qs.config === "string") {
          newSession.environmentConfigYaml = qs.config;
        }
        if (typeof qs.mode === "string") {
          newSession.mode = qs.mode;
        }
        if (qs.solidSubset instanceof Array) {
          newSession.solidSubset = qs.solidSubset;
        } else if (typeof qs.solidSubset === "string") {
          newSession.solidSubset = [qs.solidSubset];
        }

        onSave(applyCreateSession(data, newSession));
        return <Redirect to={`/${params.pipelineName}/execute`} />;
      }

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

            if (
              !pipelineOrError ||
              pipelineOrError.__typename === "PipelineNotFoundError"
            ) {
              return (
                <NonIdealState
                  icon={IconNames.FLOW_BRANCH}
                  title="Pipeline Not Found"
                  description={
                    pipelineOrError
                      ? pipelineOrError.message
                      : "No data returned from GraphQL"
                  }
                />
              );
            }

            if (pipelineOrError.__typename === "PythonError") {
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
                pipelineName={params.pipelineName}
                currentSession={data.sessions[data.current]}
              />
            );
          }}
        </Query>
      );
    }}
  </StorageProvider>
);

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
  }

  ${PipelineExecutionContainer.fragments.PipelineExecutionContainerFragment}
`;
