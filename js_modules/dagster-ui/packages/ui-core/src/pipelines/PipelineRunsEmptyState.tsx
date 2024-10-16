import {Box, Icon, NonIdealState} from '@dagster-io/ui-components';

import {AnchorButton} from '../ui/AnchorButton';
import {isThisThingAnAssetJob, useRepository} from '../workspace/WorkspaceContext/util';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface EmptyStateProps {
  repoAddress: RepoAddress | null;
  jobName: string;
  jobPath: string;
  anyFilter: boolean;
}

export const PipelineRunsEmptyState = (props: EmptyStateProps) => {
  const {repoAddress, anyFilter, jobName, jobPath} = props;

  const repo = useRepository(repoAddress);
  const isAssetJob = isThisThingAnAssetJob(repo, jobName);

  const description = () => {
    if (!repoAddress) {
      return <div>You have not launched any runs for this job.</div>;
    }

    if (isAssetJob) {
      return (
        <Box flex={{direction: 'column', gap: 12}}>
          <div>
            {anyFilter
              ? 'There are no matching runs for these filters.'
              : 'You have not materialized any assets with this job yet.'}
          </div>
          <div>
            <AnchorButton
              icon={<Icon name="materialization" />}
              to={workspacePathFromAddress(repoAddress, `/jobs/${jobPath}`)}
            >
              Materialize an asset
            </AnchorButton>
          </div>
        </Box>
      );
    }

    return (
      <Box flex={{direction: 'column', gap: 12}}>
        <div>
          {anyFilter
            ? 'There are no matching runs for these filters.'
            : 'You have not launched any runs for this job yet.'}
        </div>
        <div>
          <AnchorButton
            icon={<Icon name="add_circle" />}
            to={workspacePathFromAddress(repoAddress, `/jobs/${jobPath}/playground`)}
          >
            Launch a run
          </AnchorButton>
        </div>
      </Box>
    );
  };

  return (
    <Box padding={{vertical: 64}}>
      <NonIdealState icon="run" title="No runs found" description={description()} />
    </Box>
  );
};
