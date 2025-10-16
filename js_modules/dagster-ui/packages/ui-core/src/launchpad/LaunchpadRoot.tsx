import {Dialog, DialogHeader} from '@dagster-io/ui-components';
import {CodeMirrorInDialogStyle} from '@dagster-io/ui-components/editor';
import {Redirect, useParams} from 'react-router-dom';

import {useQuery} from '../apollo-client';
import {LaunchpadAllowedRoot, PIPELINE_EXECUTION_ROOT_QUERY} from './LaunchpadAllowedRoot';
import {LaunchpadConfig} from './LaunchpadSession';
import {LaunchpadSessionError} from './LaunchpadSessionError';
import {LaunchpadSessionLoading} from './LaunchpadSessionLoading';
import {LaunchpadTransientSessionContainer} from './LaunchpadTransientSessionContainer';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {asAssetKeyInput} from '../assets/asInput';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {RepoAddress} from '../workspace/types';
import {LaunchpadRootQuery, LaunchpadRootQueryVariables} from './types/LaunchpadAllowedRoot.types';
import {AssetKey} from '../graphql/types';

// ########################
// ##### LAUNCHPAD ROOTS
// ########################

export const AssetLaunchpad = ({
  repoAddress,
  sessionPresets,
  assetJobName,
  open,
  setOpen,
}: {
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
  assetJobName: string;
  open: boolean;
  setOpen: (open: boolean) => void;
}) => {
  const title = 'Launchpad (configure assets)';

  return (
    <Dialog
      style={{height: '90vh', width: '80%'}}
      isOpen={open}
      canEscapeKeyClose={false}
      canOutsideClickClose={true}
      onClose={() => setOpen(false)}
    >
      <DialogHeader icon="layers" label={title} />
      <CodeMirrorInDialogStyle />
      <LaunchpadAllowedRoot
        launchpadType="asset"
        pipelinePath={assetJobName}
        repoAddress={repoAddress}
        sessionPresets={sessionPresets}
      />
    </Dialog>
  );
};

export const BackfillLaunchpad = ({
  repoAddress,
  sessionPresets,
  assetJobName,
  assetKeys,
  open,
  setOpen,
  onSaveConfig,
  savedConfig,
}: {
  repoAddress: RepoAddress;
  sessionPresets?: Partial<IExecutionSession>;
  assetJobName: string;
  assetKeys?: AssetKey[];
  open: boolean;
  setOpen: (open: boolean) => void;
  onSaveConfig: (config: LaunchpadConfig) => void;
  savedConfig?: LaunchpadConfig | null;
}) => {
  const title = 'Config Editor';

  // Convert assetKeys to the format expected by sessionPresets.assetSelection
  const assetSelection = assetKeys?.map((assetKey) => ({
    assetKey: {path: assetKey.path},
  }));

  const result = useQuery<LaunchpadRootQuery, LaunchpadRootQueryVariables>(
    PIPELINE_EXECUTION_ROOT_QUERY,
    {
      variables: {
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
        pipelineName: assetJobName,
        assetSelection: assetSelection?.map(asAssetKeyInput) || null,
      },
    },
  );

  if (result?.loading) {
    return <LaunchpadSessionLoading />;
  }

  const pipelineOrError = result?.data?.pipelineOrError;
  const partitionSetsOrError = result?.data?.partitionSetsOrError;
  if (
    pipelineOrError?.__typename !== 'Pipeline' ||
    partitionSetsOrError?.__typename !== 'PartitionSets'
  ) {
    return (
      <LaunchpadSessionError
        icon="error"
        title="Error loading base asset job"
        description={
          pipelineOrError?.__typename === 'PythonError' ? pipelineOrError.message : 'Unknown error'
        }
      />
    );
  }

  // Use the saved config's runConfigYaml as rootDefaultYaml if available
  const rootDefaultYaml = savedConfig?.runConfigYaml;

  return (
    <Dialog
      style={{height: '90vh', width: '80%', minWidth: '1000px'}}
      isOpen={open}
      onClose={() => setOpen(false)}
    >
      <DialogHeader icon="layers" label={title} />
      <CodeMirrorInDialogStyle />
      <LaunchpadTransientSessionContainer
        launchpadType="asset"
        pipeline={pipelineOrError}
        partitionSets={partitionSetsOrError}
        repoAddress={repoAddress}
        sessionPresets={{
          ...sessionPresets,
          assetSelection,
        }}
        rootDefaultYaml={rootDefaultYaml}
        onSaveConfig={onSaveConfig}
        runConfigSchema={
          result.data?.runConfigSchemaOrError.__typename === 'RunConfigSchema'
            ? result.data.runConfigSchemaOrError
            : undefined
        }
      />
    </Dialog>
  );
};

export const JobOrAssetLaunchpad = (props: {repoAddress: RepoAddress}) => {
  const {repoAddress} = props;
  const {pipelinePath, repoPath} = useParams<{repoPath: string; pipelinePath: string}>();
  const {
    permissions: {canLaunchPipelineExecution},
    loading,
  } = usePermissionsForLocation(repoAddress.location);
  useBlockTraceUntilTrue('Permissions', !loading);

  if (loading) {
    return null;
  }

  if (!canLaunchPipelineExecution) {
    return <Redirect to={`/locations/${repoPath}/pipeline_or_job/${pipelinePath}`} />;
  }

  return (
    <LaunchpadAllowedRoot
      launchpadType={pipelinePath.includes(__ASSET_JOB_PREFIX) ? 'asset' : 'job'}
      pipelinePath={pipelinePath}
      repoAddress={repoAddress}
    />
  );
};
