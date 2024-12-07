import {Dialog, DialogHeader} from '@dagster-io/ui-components';
import {CodeMirrorInDialogStyle} from '@dagster-io/ui-components/editor';
import {Redirect, useParams} from 'react-router-dom';

import {LaunchpadAllowedRoot} from './LaunchpadAllowedRoot';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {RepoAddress} from '../workspace/types';

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

export const JobOrAssetLaunchpad = (props: {repoAddress: RepoAddress}) => {
  const {repoAddress} = props;
  const {pipelinePath, repoPath} = useParams<{repoPath: string; pipelinePath: string}>();
  const {
    permissions: {canLaunchPipelineExecution},
    loading,
  } = usePermissionsForLocation(repoAddress.location);
  useBlockTraceUntilTrue('Permissions', loading);

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
