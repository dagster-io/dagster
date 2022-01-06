import {gql, useLazyQuery} from '@apollo/client';
import * as React from 'react';

import {DISABLED_MESSAGE, usePermissions} from '../app/Permissions';
import {canRunAllSteps, canRunFromFailure} from '../runs/RunActionButtons';
import {RunFragments} from '../runs/RunFragments';
import {useJobReExecution} from '../runs/useJobReExecution';
import {ButtonWIP} from '../ui/Button';
import {IconWIP} from '../ui/Icon';
import {MenuWIP, MenuLink, MenuItemWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {Tooltip} from '../ui/Tooltip';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {OverviewJobFragment} from './types/OverviewJobFragment';
import {RunReExecutionQuery} from './types/RunReExecutionQuery';

interface Props {
  job: OverviewJobFragment;
  repoAddress: RepoAddress;
}

/**
 * Lazily load more information about the last run for this job, then use that data to inform
 * whether re-execution is possible.
 */
export const JobMenu = (props: Props) => {
  const {job, repoAddress} = props;
  const lastRun = job.runs[0];
  const {canLaunchPipelineReexecution} = usePermissions();
  const [fetchHasExecutionPlan, {data}] = useLazyQuery<RunReExecutionQuery>(RUN_RE_EXECUTION_QUERY);

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data?.pipelineRunOrError : null;

  const fetchIfPossible = React.useCallback(() => {
    if (lastRun.id) {
      fetchHasExecutionPlan({variables: {runId: lastRun.id}});
    }
  }, [lastRun, fetchHasExecutionPlan]);

  const onLaunch = useJobReExecution(run);

  const reExecuteAllItem = (
    <MenuItemWIP
      icon="replay"
      text="Re-execute latest run"
      onClick={() => onLaunch({type: 'all'})}
      disabled={!canLaunchPipelineReexecution || !run || !canRunAllSteps(run)}
    />
  );

  const reExecuteFromFailureItem = (
    <MenuItemWIP
      icon="sync_problem"
      text="Re-execute latest run from failure"
      onClick={() => onLaunch({type: 'from-failure'})}
      disabled={!canLaunchPipelineReexecution || !run || !canRunFromFailure(run)}
    />
  );

  return (
    <Popover
      onOpened={() => fetchIfPossible()}
      content={
        <MenuWIP>
          <MenuLink
            to={workspacePipelinePath({
              repoName: repoAddress.name,
              repoLocation: repoAddress.location,
              pipelineName: job.name,
              isJob: job.isJob,
            })}
            icon="job"
            text="View job"
          />
          <MenuLink
            to={workspacePipelinePath({
              repoName: repoAddress.name,
              repoLocation: repoAddress.location,
              pipelineName: job.name,
              isJob: job.isJob,
              path: '/runs',
            })}
            icon="checklist"
            text="View all recent runs"
          />
          {canLaunchPipelineReexecution ? (
            reExecuteAllItem
          ) : (
            <Tooltip content={DISABLED_MESSAGE} display="block">
              {reExecuteAllItem}
            </Tooltip>
          )}
          {canLaunchPipelineReexecution ? (
            reExecuteFromFailureItem
          ) : (
            <Tooltip content={DISABLED_MESSAGE} display="block">
              {reExecuteFromFailureItem}
            </Tooltip>
          )}
        </MenuWIP>
      }
      position="bottom-right"
    >
      <ButtonWIP icon={<IconWIP name="expand_more" />} />
    </Popover>
  );
};

const RUN_RE_EXECUTION_QUERY = gql`
  query RunReExecutionQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        ...RunFragment
      }
    }
  }

  ${RunFragments.RunFragment}
`;
