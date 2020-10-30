import {gql} from '@apollo/client';
import {Query} from '@apollo/client/react/components';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Redirect} from 'react-router-dom';

import {
  IExecutionSessionChanges,
  applyChangesToSession,
  applyCreateSession,
  useStorage,
} from 'src/LocalStorage';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {
  ExecutionSessionContainer,
  ExecutionSessionContainerError,
  ExecutionSessionContainerLoading,
} from 'src/execute/ExecutionSessionContainer';
import {ExecutionTabs} from 'src/execute/ExecutionTabs';
import {
  PipelineExecutionConfigSchemaQuery,
  PipelineExecutionConfigSchemaQueryVariables,
} from 'src/execute/types/PipelineExecutionConfigSchemaQuery';
import {
  PipelineExecutionRootQuery,
  PipelineExecutionRootQueryVariables,
} from 'src/execute/types/PipelineExecutionRootQuery';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const PipelineExecutionRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;
  const {pipelineName, snapshotId} = explorerPathFromString(pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const [data, onSave] = useStorage(repoAddress.name || '', pipelineName);

  const session = data.sessions[data.current];
  const pipelineSelector = {
    ...repoAddressToSelector(repoAddress),
    pipelineName,
    solidSelection: session?.solidSelection || undefined,
  };

  if (snapshotId) {
    return (
      <Redirect
        to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/playground`)}
      />
    );
  }

  const onSaveSession = (session: string, changes: IExecutionSessionChanges) => {
    onSave(applyChangesToSession(data, session, changes));
  };

  const {name: repositoryName, location: repositoryLocationName} = repoAddress;

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
                  repoAddress={repoAddress}
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
