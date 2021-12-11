import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {
  CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT,
  CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT,
} from './ConfigEditorConfigPicker';
import {LaunchpadSessionError} from './LaunchpadSessionError';
import {LaunchpadSessionLoading} from './LaunchpadSessionLoading';
import {LaunchpadRootQuery} from './types/LaunchpadRootQuery';

const LaunchpadSessionContainer = React.lazy(() => import('./LaunchpadSessionContainer'));

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const LaunchpadRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;
  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath(props);

  const {name: repositoryName, location: repositoryLocationName} = repoAddress;

  const result = useQuery<LaunchpadRootQuery>(PIPELINE_EXECUTION_ROOT_QUERY, {
    variables: {repositoryName, repositoryLocationName, pipelineName},
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
  });

  const pipelineOrError = result?.data?.pipelineOrError;
  const partitionSetsOrError = result?.data?.partitionSetsOrError;

  if (!pipelineOrError || !partitionSetsOrError) {
    return <LaunchpadSessionLoading />;
  }

  if (
    partitionSetsOrError.__typename === 'PipelineNotFoundError' ||
    pipelineOrError.__typename === 'PipelineNotFoundError'
  ) {
    const message =
      pipelineOrError.__typename === 'PipelineNotFoundError'
        ? pipelineOrError.message
        : 'No data returned from GraphQL';

    return pipelineName !== '' ? (
      <LaunchpadSessionError
        icon="error"
        title={isJob ? 'Job not found' : 'Pipeline not found'}
        description={message}
      />
    ) : (
      <LaunchpadSessionError
        icon="no-results"
        title={isJob ? 'Select a job' : 'Select a pipeline'}
        description={message}
      />
    );
  }

  if (pipelineOrError && pipelineOrError.__typename === 'InvalidSubsetError') {
    throw new Error(`Should never happen because we do not request a subset`);
  }

  if (pipelineOrError && pipelineOrError.__typename === 'PythonError') {
    return (
      <LaunchpadSessionError
        icon="error"
        title="Python Error"
        description={pipelineOrError.message}
      />
    );
  }
  if (partitionSetsOrError && partitionSetsOrError.__typename === 'PythonError') {
    return (
      <LaunchpadSessionError
        icon="error"
        title="Python Error"
        description={partitionSetsOrError.message}
      />
    );
  }

  return (
    <React.Suspense fallback={<div />}>
      <LaunchpadSessionContainer
        pipeline={pipelineOrError}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
      />
    </React.Suspense>
  );
};

const EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT = gql`
  fragment LaunchpadSessionContainerPipelineFragment on Pipeline {
    id
    isJob
    ...ConfigEditorGeneratorPipelineFragment
    modes {
      id
      name
      description
    }
  }
  ${CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT}
`;

const EXECUTION_SESSION_CONTAINER_PARTITION_SETS_FRAGMENT = gql`
  fragment LaunchpadSessionContainerPartitionSetsFragment on PartitionSets {
    ...ConfigEditorGeneratorPartitionSetsFragment
  }
  ${CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT}
`;

const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query LaunchpadRootQuery(
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
        ...LaunchpadSessionContainerPipelineFragment
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
      ...LaunchpadSessionContainerPartitionSetsFragment
      ... on PipelineNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }

  ${EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT}
  ${EXECUTION_SESSION_CONTAINER_PARTITION_SETS_FRAGMENT}
`;
