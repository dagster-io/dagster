import * as yaml from 'yaml';

import {
  CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT,
  CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT,
} from './ConfigEditorConfigPicker';
import {LaunchpadConfig, PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY} from './LaunchpadSession';
import {LaunchpadSessionError} from './LaunchpadSessionError';
import {LaunchpadSessionLoading} from './LaunchpadSessionLoading';
import {LaunchpadTransientSessionContainer} from './LaunchpadTransientSessionContainer';
import {LaunchpadType} from './types';
import {gql, useQuery} from '../apollo-client';
import {LaunchpadRootQuery, LaunchpadRootQueryVariables} from './types/LaunchpadAllowedRoot.types';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {useTrackPageView} from '../app/analytics';
import {explorerPathFromString, useStripSnapshotFromPath} from '../pipelines/PipelinePathUtils';
import {useJobTitle} from '../pipelines/useJobTitle';
import {lazy} from '../util/lazy';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import * as React from 'react';

import {
  PipelineExecutionConfigSchemaQuery,
  PipelineExecutionConfigSchemaQueryVariables
} from './types/LaunchpadSession.types';
import {asAssetKeyInput} from '../assets/asInput';
import {
  PipelineSelector
} from '../graphql/types';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';

const LaunchpadStoredSessionsContainer = lazy(() => import('./LaunchpadStoredSessionsContainer'));

interface Props {
  launchpadType: LaunchpadType;
  pipelinePath: string;
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
  onSaveConfig?: (config: LaunchpadConfig) => void;
}

const filterDefaultYamlForSubselection = (defaultYaml: string, opNames: Set<string>): string => {
  const parsedYaml = yaml.parse(defaultYaml);

  const opsConfig = parsedYaml['ops'];
  if (opsConfig) {
    const filteredOpKeys = Object.keys(opsConfig).filter((entry: any) => {
      return opNames.has(entry);
    });
    const filteredOpsConfig = Object.fromEntries(
      filteredOpKeys.map((key) => [key, opsConfig[key]]),
    );
    parsedYaml['ops'] = filteredOpsConfig;
  }

  return yaml.stringify(parsedYaml);
};

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
      variables: {repositoryName, repositoryLocationName, pipelineName},
    },
  );
  const pipelineSelector: PipelineSelector = React.useMemo(() => {
    return {
      ...repoAddressToSelector(repoAddress),
      pipelineName: pipelineName,
      assetSelection: sessionPresets?.assetSelection?.map(asAssetKeyInput) || [],
      assetCheckSelection: [],
    };
  }, [
    sessionPresets?.assetSelection,
    pipelineName,
    repoAddress,
  ]);

  const configResult = useQuery<
    PipelineExecutionConfigSchemaQuery,
    PipelineExecutionConfigSchemaQueryVariables
  >(PIPELINE_EXECUTION_CONFIG_SCHEMA_QUERY, {
    variables: {selector: pipelineSelector, mode: sessionPresets?.mode},
  });


  const pipelineOrError = result?.data?.pipelineOrError;
  const partitionSetsOrError = result?.data?.partitionSetsOrError;

  const runConfigSchemaOrError = result.data?.runConfigSchemaOrError;

  const rootDefaultYaml = configResult?.data?.runConfigSchemaOrError?.rootDefaultYaml;


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


  console.log('runConfigSchemaOrError', runConfigSchemaOrError);
  if (launchpadType === 'asset') {
    return (
      <LaunchpadTransientSessionContainer
        launchpadType={launchpadType}
        pipeline={pipelineOrError}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
        sessionPresets={sessionPresets || {}}
        rootDefaultYaml={rootDefaultYaml}
        onSaveConfig={onSaveConfig}
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
      />
    );
  }
};

export const PIPELINE_EXECUTION_ROOT_QUERY = gql`
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
      }
    ) {
      __typename
      ... on RunConfigSchema {
        rootDefaultYaml
      }
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

  ${PYTHON_ERROR_FRAGMENT}
  ${CONFIG_EDITOR_GENERATOR_PARTITION_SETS_FRAGMENT}
  ${CONFIG_EDITOR_GENERATOR_PIPELINE_FRAGMENT}
`;
