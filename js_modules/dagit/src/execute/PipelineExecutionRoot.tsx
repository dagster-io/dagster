import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import ExecutionSessionContainer, {
  ExecutionSessionContainerError
} from "./ExecutionSessionContainer";
import { QueryResult, Query } from "react-apollo";
import { NonIdealState, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import {
  useStorage,
  IExecutionSessionChanges,
  applyChangesToSession,
  applyCreateSession
} from "../LocalStorage";
import { PipelineExecutionRootQuery } from "./types/PipelineExecutionRootQuery";
import { ExecutionTabs } from "./ExecutionTabs";
import { RouteComponentProps } from "react-router-dom";

export const PipelineExecutionRoot: React.FunctionComponent<RouteComponentProps<{
  pipelineSelector: string;
}>> = ({ match }) => {
  const pipelineName = match.params.pipelineSelector.split(":")[0];
  const [data, onSave] = useStorage(pipelineName);

  const vars = {
    name: pipelineName,
    mode: data.sessions[data.current]?.mode,
    solidSubset: data.sessions[data.current]?.solidSubset
  };

  const onSaveSession = (
    session: string,
    changes: IExecutionSessionChanges
  ) => {
    onSave(applyChangesToSession(data, session, changes));
  };

  return (
    <PipelineExecutionWrapper>
      <TabBarContainer>
        <ExecutionTabs data={data} onSave={onSave} />
        <div style={{ flex: 1 }} />
      </TabBarContainer>
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
            environmentSchemaOrError?.__typename === "PipelineNotFoundError" ||
            pipelineOrError?.__typename === "PipelineNotFoundError"
          ) {
            const message =
              pipelineOrError?.__typename === "PipelineNotFoundError"
                ? pipelineOrError.message
                : "No data returned from GraphQL";

            return (
              <ExecutionSessionContainerError
                currentSession={data.sessions[data.current]}
                onSaveSession={changes => onSaveSession(data.current, changes)}
              >
                {vars.name !== "" ? (
                  <NonIdealState
                    icon={IconNames.FLOW_BRANCH}
                    title="Pipeline Not Found"
                    description={message}
                  />
                ) : (
                  <NonIdealState
                    icon={IconNames.FLOW_BRANCH}
                    title="Select a Pipeline"
                  />
                )}
              </ExecutionSessionContainerError>
            );
          }

          if (pipelineOrError && pipelineOrError.__typename === "PythonError") {
            return (
              <ExecutionSessionContainerError
                currentSession={data.sessions[data.current]}
                onSaveSession={changes => onSaveSession(data.current, changes)}
              >
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Python Error"
                  description={pipelineOrError.message}
                />
              </ExecutionSessionContainerError>
            );
          }

          if (!pipelineOrError) {
            return (
              <ExecutionSessionContainerError
                currentSession={data.sessions[data.current]}
                onSaveSession={changes => onSaveSession(data.current, changes)}
              ></ExecutionSessionContainerError>
            );
          }

          return (
            <ExecutionSessionContainer
              data={data}
              onSaveSession={changes => onSaveSession(data.current, changes)}
              onCreateSession={initial =>
                onSave(applyCreateSession(data, initial))
              }
              pipelineOrError={pipelineOrError}
              environmentSchemaOrError={environmentSchemaOrError}
              currentSession={data.sessions[data.current]}
            />
          );
        }}
      </Query>
    </PipelineExecutionWrapper>
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
      ...ExecutionSessionContainerFragment
    }
    environmentSchemaOrError(
      selector: { name: $name, solidSubset: $solidSubset }
      mode: $mode
    ) {
      ...ExecutionSessionContainerEnvironmentSchemaFragment
    }
  }

  ${ExecutionSessionContainer.fragments.ExecutionSessionContainerFragment}
  ${ExecutionSessionContainer.fragments.EnvironmentSchemaOrErrorFragment}
`;

const PipelineExecutionWrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
`;

const TabBarContainer = styled.div`
  height: 45px;
  display: flex;
  flex-direction: row;
  align-items: center;
  border-bottom: 1px solid ${Colors.GRAY5};
  background: ${Colors.LIGHT_GRAY3};
  padding: 2px 10px;
  z-index: 3;
`;
