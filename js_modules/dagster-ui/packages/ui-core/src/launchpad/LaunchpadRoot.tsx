import {Dialog, DialogHeader} from '@dagster-io/ui-components';
import {CodeMirrorInDialogStyle} from '@dagster-io/ui-components/editor';
import {Redirect, useParams} from 'react-router-dom';

import {LaunchpadAllowedRoot} from './LaunchpadAllowedRoot';
import {IExecutionSession} from '../app/ExecutionSessionStorage';
import {usePermissionsForLocation} from '../app/Permissions';
import {__ASSET_JOB_PREFIX} from '../asset-graph/Utils';
import {RepositorySelector} from '../graphql/types';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

// ########################
// ##### LAUNCHPAD ROOTS
// ########################

export const AssetLaunchpad = ({
  repositorySelector,
  sessionPresets,
  assetJobName,
  open,
  setOpen,
}: {
  repositorySelector: RepositorySelector;
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
        repositorySelector={repositorySelector}
        sessionPresets={sessionPresets}
      />
    </Dialog>
  );
};

export const JobOrAssetLaunchpad = (props: {repositorySelector: RepositorySelector}) => {
  const {repositorySelector} = props;
  const {pipelinePath, repoPath} = useParams<{repoPath: string; pipelinePath: string}>();
  const {
    permissions: {canLaunchPipelineExecution},
    loading,
  } = usePermissionsForLocation(repositorySelector.repositoryLocationName);
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
      repositorySelector={repositorySelector}
    />
  );
};
