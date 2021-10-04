import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {RepoAddress} from '../workspace/types';

import {
  CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT,
  CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT,
} from './ConfigEditorConfigPicker';
import {ExecutionSessionContainerError} from './ExecutionSessionContainerError';
import {ExecutionSessionContainerLoading} from './ExecutionSessionContainerLoading';
import {PipelineExecutionRootQuery} from './types/PipelineExecutionRootQuery';

const ExecutionSessionContainer = React.lazy(() => import('./ExecutionSessionContainer'));

interface Props {
  pipelinePath: string;
  repoAddress: RepoAddress;
}

export const PipelineExecutionRoot: React.FC<Props> = (props) => {
  const {pipelinePath, repoAddress} = props;
  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName, pipelineMode} = explorerPath;
  const {flagPipelineModeTuples} = useFeatureFlags();
  useJobTitle(explorerPath);
  useStripSnapshotFromPath(props);

  const {name: repositoryName, location: repositoryLocationName} = repoAddress;

  const result = useQuery<PipelineExecutionRootQuery>(PIPELINE_EXECUTION_ROOT_QUERY, {
    variables: {repositoryName, repositoryLocationName, pipelineName},
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
  });

  const pipelineOrError = result?.data?.pipelineOrError;
  const partitionSetsOrError = result?.data?.partitionSetsOrError;

  if (!pipelineOrError || !partitionSetsOrError) {
    return <ExecutionSessionContainerLoading />;
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
      <ExecutionSessionContainerError
        icon="error"
        title={flagPipelineModeTuples ? 'Job not found' : 'Pipeline not found'}
        description={message}
      />
    ) : (
      <ExecutionSessionContainerError
        icon="error"
        title={flagPipelineModeTuples ? 'Select a job' : 'Select a pipeline'}
      />
    );
  }

  if (pipelineOrError && pipelineOrError.__typename === 'InvalidSubsetError') {
    throw new Error(`Should never happen because we do not request a subset`);
  }

  if (pipelineOrError && pipelineOrError.__typename === 'PythonError') {
    return (
      <ExecutionSessionContainerError
        icon="error"
        title="Python Error"
        description={pipelineOrError.message}
      />
    );
  }
  if (partitionSetsOrError && partitionSetsOrError.__typename === 'PythonError') {
    return (
      <ExecutionSessionContainerError
        icon="error"
        title="Python Error"
        description={partitionSetsOrError.message}
      />
    );
  }

  return (
    <React.Suspense fallback={<div />}>
      <ExecutionSessionContainer
        pipeline={pipelineOrError}
        pipelineMode={flagPipelineModeTuples ? pipelineMode : undefined}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
      />
    </React.Suspense>
  );
};

const EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT = gql`
  fragment ExecutionSessionContainerPipelineFragment on Pipeline {
    id
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
  fragment ExecutionSessionContainerPartitionSetsFragment on PartitionSets {
    ...ConfigEditorGeneratorPartitionSetsFragment
  }
  ${CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT}
`;

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

  ${EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT}
  ${EXECUTION_SESSION_CONTAINER_PARTITION_SETS_FRAGMENT}
`;
