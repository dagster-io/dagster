import * as React from 'react';
import gql from 'graphql-tag';
import ExecutionSessionContainer, {
  ExecutionSessionContainerError,
  ExecutionSessionContainerLoading,
} from './ExecutionSessionContainer';
import {Query} from 'react-apollo';
import {IconNames} from '@blueprintjs/icons';
import {
  useStorage,
  IExecutionSessionChanges,
  applyChangesToSession,
  applyCreateSession,
} from '../LocalStorage';
import {
  PipelineExecutionRootQuery,
  PipelineExecutionRootQueryVariables,
} from './types/PipelineExecutionRootQuery';
import {ExecutionTabs} from './ExecutionTabs';
import {RouteComponentProps} from 'react-router-dom';
import {usePipelineSelector, useRepositorySelector} from '../DagsterRepositoryContext';
import {
  PipelineExecutionConfigSchemaQuery,
  PipelineExecutionConfigSchemaQueryVariables,
} from './types/PipelineExecutionConfigSchemaQuery';

export const PipelineExecutionRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({match}) => {
  const pipelineName = match.params.pipelinePath.split(':')[0];
  const {repositoryName, repositoryLocationName} = useRepositorySelector();
  const [data, onSave] = useStorage(repositoryName, pipelineName);

  const session = data.sessions[data.current];
  const pipelineSelector = usePipelineSelector(pipelineName, session?.solidSelection || undefined);

  const onSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    onSave(applyChangesToSession(data, session, changes));
  };

  return (
    <>
      <ExecutionTabs data={data} onSave={onSave} />
      <Query<PipelineExecutionRootQuery, PipelineExecutionRootQueryVariables>
        // never serve cached Pipeline given new vars by forcing teardown of the Query.
        // Apollo's behaviors are sort of whacky, even with no-cache. Should just use
        // window.fetch...
        key={JSON.stringify({
          repositoryName,
          repositoryLocationName,
          pipelineName,
        })}
        variables={{repositoryName, repositoryLocationName, pipelineName}}
        query={PIPELINE_EXECUTION_ROOT_QUERY}
        fetchPolicy="cache-and-network"
        partialRefetch={true}
      >
        {(result) => (
          <Query<PipelineExecutionConfigSchemaQuery, PipelineExecutionConfigSchemaQueryVariables>
            key={JSON.stringify({pipelineSelector, mode: session?.mode})}
            variables={{selector: pipelineSelector, mode: session?.mode}}
            query={PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY}
            fetchPolicy="cache-and-network"
            partialRefetch={true}
          >
            {(configResult) => {
              const pipelineOrError = result.data && result.data.pipelineOrError;
              const partitionSetsOrError = result.data && result.data.partitionSetsOrError;
              const configSchemaOrError =
                configResult.data && configResult.data.runConfigSchemaOrError;

              if (!pipelineOrError || !partitionSetsOrError) {
                return <ExecutionSessionContainerLoading />;
              }

              if (
                configSchemaOrError?.__typename === 'PipelineNotFoundError' ||
                partitionSetsOrError.__typename === 'PipelineNotFoundError' ||
                pipelineOrError.__typename === 'PipelineNotFoundError'
              ) {
                const message =
                  pipelineOrError.__typename === 'PipelineNotFoundError'
                    ? pipelineOrError.message
                    : 'No data returned from GraphQL';

                return pipelineName !== '' ? (
                  <ExecutionSessionContainerError
                    icon={IconNames.FLOW_BRANCH}
                    title="Pipeline Not Found"
                    description={message}
                  />
                ) : (
                  <ExecutionSessionContainerError
                    icon={IconNames.FLOW_BRANCH}
                    title="Select a Pipeline"
                  />
                );
              }

              if (pipelineOrError && pipelineOrError.__typename === 'InvalidSubsetError') {
                throw new Error(`Should never happen because we do not request a subset`);
              }

              if (pipelineOrError && pipelineOrError.__typename === 'PythonError') {
                return (
                  <ExecutionSessionContainerError
                    icon={IconNames.ERROR}
                    title="Python Error"
                    description={pipelineOrError.message}
                  />
                );
              }
              if (partitionSetsOrError && partitionSetsOrError.__typename === 'PythonError') {
                return (
                  <ExecutionSessionContainerError
                    icon={IconNames.ERROR}
                    title="Python Error"
                    description={partitionSetsOrError.message}
                  />
                );
              }

              return (
                <ExecutionSessionContainer
                  data={data}
                  onSaveSession={(changes) => onSaveSession(data.current, changes)}
                  onCreateSession={(initial) => onSave(applyCreateSession(data, initial))}
                  pipeline={pipelineOrError}
                  partitionSets={partitionSetsOrError}
                  runConfigSchemaOrError={configSchemaOrError}
                  currentSession={session}
                  pipelineSelector={pipelineSelector}
                />
              );
            }}
          </Query>
        )}
      </Query>
    </>
  );
};

const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query PipelineExecutionRootQuery(
    $pipelineName: String!
    $repositoryName: String!
    $repositoryLocationName: String!
  ) {
    pipelineOrError(
      params: {
        pipelineName: $pipelineName
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      ... on PipelineNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
      ... on Pipeline {
        id
        ...ExecutionSessionContainerPipelineFragment
      }
    }
    partitionSetsOrError(
      pipelineName: $pipelineName
      repositorySelector: {
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      __typename
      ...ExecutionSessionContainerPartitionSetsFragment
      ... on PipelineNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }

  ${ExecutionSessionContainer.fragments.ExecutionSessionContainerPipelineFragment}
  ${ExecutionSessionContainer.fragments.ExecutionSessionContainerPartitionSetsFragment}
`;

const PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY = gql`
  query PipelineExecutionConfigSchemaQuery($selector: PipelineSelector!, $mode: String) {
    runConfigSchemaOrError(selector: $selector, mode: $mode) {
      ...ExecutionSessionContainerRunConfigSchemaFragment
    }
  }

  ${ExecutionSessionContainer.fragments.RunConfigSchemaOrErrorFragment}
`;
