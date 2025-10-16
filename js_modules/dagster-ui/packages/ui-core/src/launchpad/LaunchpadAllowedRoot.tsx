import {
  CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT,
  CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT,
} from './ConfigEditorConfigPicker';
import {LaunchpadConfig} from './LaunchpadSession';
import {LaunchpadSessionError} from './LaunchpadSessionError';
import {LaunchpadSessionLoading} from './LaunchpadSessionLoading';
import {LaunchpadTransientSessionContainer} from './LaunchpadTransientSessionContainer';
import {LaunchpadType} from './types';
import {gql, useQuery} from '../apollo-client';
import {LaunchpadRootQuery, LaunchpadRootQueryVariables} from './types/LaunchpadAllowedRoot.types';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {asAssetKeyInput} from '../assets/asInput';
import {CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT} from '../configeditor/ConfigEditorUtils';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {lazy} from '../util/lazy';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';

const LaunchpadStoredSessionsContainer = lazy(() => import('./LaunchpadStoredSessionsContainer'));

interface Props {
  launchpadType: LaunchpadType;
  pipelinePath: string;
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
  onSaveConfig?: (config: LaunchpadConfig) => void;
}

export const LaunchpadAllowedRoot = (props: Props) => {
  useTrackPageView();

  const {pipelinePath, repoAddress, launchpadType, sessionPresets, onSaveConfig} = props;
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
      variables: {
        repositoryName,
        repositoryLocationName,
        pipelineName,
        assetSelection: sessionPresets?.assetSelection?.map(asAssetKeyInput) || null,
      },
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

  if (
    pipelineOrError.__typename === 'PythonError' ||
    pipelineOrError.__typename === 'InvalidSubsetError'
  ) {
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
        rootDefaultYaml={
          result.data?.runConfigSchemaOrError.__typename === 'RunConfigSchema'
            ? result.data.runConfigSchemaOrError.rootDefaultYaml
            : undefined
        }
        onSaveConfig={onSaveConfig}
        runConfigSchema={
          result.data?.runConfigSchemaOrError.__typename === 'RunConfigSchema'
            ? result.data.runConfigSchemaOrError
            : undefined
        }
      />
    );
  } else {
    // job
    return (
      <LaunchpadStoredSessionsContainer
        launchpadType={launchpadType}
        pipeline={pipelineOrError}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
        rootDefaultYaml={
          result.data?.runConfigSchemaOrError.__typename === 'RunConfigSchema'
            ? result.data.runConfigSchemaOrError.rootDefaultYaml
            : undefined
        }
        runConfigSchema={
          result.data?.runConfigSchemaOrError.__typename === 'RunConfigSchema'
            ? result.data.runConfigSchemaOrError
            : undefined
        }
      />
    );
  }
};

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
  query LaunchpadRootQuery(
    $pipelineName: String!
    $repositoryName: String!
    $repositoryLocationName: String!
    $assetSelection: [AssetKeyInput!]
  ) {
    pipelineOrError(
      params: {
        pipelineName: $pipelineName
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
        assetSelection: $assetSelection
      }
    ) {
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on Pipeline {
        id
        ...LaunchpadSessionPipelineFragment
      }
      ...PythonErrorFragment
    }
    partitionSetsOrError(
      pipelineName: $pipelineName
      repositorySelector: {
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
      }
    ) {
      ... on PipelineNotFoundError {
        message
      }
      ...LaunchpadSessionPartitionSetsFragment
      ...PythonErrorFragment
    }
    runConfigSchemaOrError(
      selector: {
        pipelineName: $pipelineName
        repositoryName: $repositoryName
        repositoryLocationName: $repositoryLocationName
        assetSelection: $assetSelection
      }
    ) {
      __typename
      ... on RunConfigSchema {
        rootDefaultYaml
      }
      ...LaunchpadSessionRunConfigSchemaFragment
    }
  }

  fragment LaunchpadSessionPartitionSetsFragment on PartitionSets {
    ...ConfigEditorGeneratorPartitionSetsFragment
  }

  fragment LaunchpadSessionPipelineFragment on Pipeline {
    id
    isJob
    isAssetJob
    ...ConfigEditorGeneratorPipelineFragment
    modes {
      id
      name
      description
    }
  }

  fragment LaunchpadSessionRunConfigSchemaFragment on RunConfigSchemaOrError {
    ... on RunConfigSchema {
      ...ConfigEditorRunConfigSchemaFragment
    }
    ... on ModeNotFoundError {
      ...LaunchpadSessionModeNotFound
    }
  }

  fragment LaunchpadSessionModeNotFound on ModeNotFoundError {
    message
  }

  ${PYTHON_ERROR_FRAGMENT}
  ${CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT}
  ${CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT}
  ${CONFIG_EDITOR_RUN_CONFIG_SCHEMA_FRAGMENT}
`;
