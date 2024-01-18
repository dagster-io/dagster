import * as React from 'react';
import {Redirect, useParams} from 'react-router-dom';

import {CodeMirrorInDialogStyle, Dialog, DialogHeader} from '@dagster-io/ui-components';

import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {RepoAddress} from '../workspace/types';
import {LaunchpadAllowedRoot} from './LaunchpadAllowedRoot';

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
      canEscapeKeyClose={true}
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
  } = usePermissionsForLocation(repoAddress.location);

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
