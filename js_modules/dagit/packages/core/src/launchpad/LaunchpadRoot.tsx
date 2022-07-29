import {gql, useQuery} from '@apollo/client';
import {Dialog, DialogHeader} from '@dagster-io/ui';
import * as React from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useTrackPageView} from '../app/analytics';
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
import {LaunchpadTransientSessionContainer} from './LaunchpadTransientSessionContainer';
import {LaunchpadRootQuery, LaunchpadRootQueryVariables} from './types/LaunchpadRootQuery';

const LaunchpadStoredSessionsContainer = React.lazy(
  () => import('./LaunchpadStoredSessionsContainer'),
);

export type LaunchpadType = 'asset' | 'job';

// ########################
// ##### LAUNCHPAD ROOTS
// ########################

export const AssetLaunchpad: React.FC<{
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
  assetJobName: string;
  open: boolean;
  setOpen: (open: boolean) => void;
}> = ({repoAddress, sessionPresets, assetJobName, open, setOpen}) => {
  const title = 'Launchpad (configure assets)';

  return (
    <Dialog
      style={{height: '90vh', width: '80%'}}
      isOpen={open}
      canEscapeKeyClose={true}
      canOutsideClickClose={true}
      onClose={() => setOpen(false)}
    >
      <DialogHeader icon="layers" label={title} />
      <LaunchpadAllowedRoot
        launchpadType="asset"
        pipelinePath={assetJobName}
        repoAddress={repoAddress}
        sessionPresets={sessionPresets}
      />
    </Dialog>
  );
};

export const JobLaunchpad: React.FC<{repoAddress: RepoAddress}> = (props) => {
  const {repoAddress} = props;
  const {pipelinePath, repoPath} = useParams<{repoPath: string; pipelinePath: string}>();
  const {canLaunchPipelineExecution} = usePermissions();

  if (!canLaunchPipelineExecution.enabled) {
    return <Redirect to={`/workspace/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
  }

  return (
    <LaunchpadAllowedRoot
      launchpadType="job"
      pipelinePath={pipelinePath}
      repoAddress={repoAddress}
    />
  );
};

// ########################
// ##### LAUNCHPAD ALLOWED ROOT
// ########################

interface Props {
  launchpadType: LaunchpadType;
  pipelinePath: string;
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
}

const LaunchpadAllowedRoot: React.FC<Props> = (props) => {
  useTrackPageView();

  const {pipelinePath, repoAddress, launchpadType, sessionPresets} = props;
  const explorerPath = explorerPathFromString(pipelinePath);
  const {pipelineName} = explorerPath;

  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, pipelineName);

  useJobTitle(explorerPath, isJob);
  useStripSnapshotFromPath(props);

  const {name: repositoryName, location: repositoryLocationName} = repoAddress;

  const result = useQuery<LaunchpadRootQuery, LaunchpadRootQueryVariables>(
    PIPELINE_EXECUTION_ROOT_QUERY,
    {
      variables: {repositoryName, repositoryLocationName, pipelineName},
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
    },
  );

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

  if (pipelineOrError.__typename === 'InvalidSubsetError') {
    throw new Error(`Should never happen because we do not request a subset`);
  }

  if (pipelineOrError.__typename === 'PythonError') {
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

  if (launchpadType === 'asset') {
    return (
      <LaunchpadTransientSessionContainer
        launchpadType={launchpadType}
        pipeline={pipelineOrError}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
        sessionPresets={sessionPresets || {}}
      />
    );
  } else {
    // job
    return (
      <React.Suspense fallback={<div />}>
        <LaunchpadStoredSessionsContainer
          launchpadType={launchpadType}
          pipeline={pipelineOrError}
          partitionSets={partitionSetsOrError}
          repoAddress={repoAddress}
        />
      </React.Suspense>
    );
  }
};

const EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT = gql`
  fragment LaunchpadSessionPipelineFragment on Pipeline {
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
  fragment LaunchpadSessionPartitionSetsFragment on PartitionSets {
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
      ...PythonErrorFragment
      ... on Pipeline {
        id
        ...LaunchpadSessionPipelineFragment
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
      ...LaunchpadSessionPartitionSetsFragment
      ... on PipelineNotFoundError {
        message
      }
      ...PythonErrorFragment
    }
  }

  ${EXECUTION_SESSION_CONTAINER_PIPELINE_FRAGMENT}
  ${EXECUTION_SESSION_CONTAINER_PARTITION_SETS_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;
