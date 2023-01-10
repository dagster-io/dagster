import {useLazyQuery} from '@apollo/client';
import {Button, Icon, Menu, MenuItem, Popover, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {graphql} from '../graphql';
import {RunTimeFragmentFragment} from '../graphql/graphql';
import {canRunAllSteps, canRunFromFailure} from '../runs/RunActionButtons';
import {useJobReExecution} from '../runs/useJobReExecution';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

interface Props {
  job: {isJob: boolean; name: string; runs: RunTimeFragmentFragment[]};
  repoAddress: RepoAddress;
}

/**
 * Lazily load more information about the last run for this job, then use that data to inform
 * whether re-execution is possible.
 */
export const JobMenu = (props: Props) => {
  const {job, repoAddress} = props;
  const lastRun = job.runs.length ? job.runs[0] : null;
  const {canLaunchPipelineReexecution} = usePermissionsForLocation(repoAddress.location);
  const [fetchHasExecutionPlan, {data}] = useLazyQuery(RUN_RE_EXECUTION_QUERY);

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data?.pipelineRunOrError : null;

  const fetchIfPossible = React.useCallback(() => {
    if (lastRun?.id) {
      fetchHasExecutionPlan({variables: {runId: lastRun.id}});
    }
  }, [lastRun, fetchHasExecutionPlan]);

  const onLaunch = useJobReExecution(run);

  const reExecuteAllItem = (
    <MenuItem
      icon="replay"
      text="Re-execute latest run"
      onClick={() => onLaunch({type: 'all'})}
      disabled={!canLaunchPipelineReexecution.enabled || !run || !canRunAllSteps(run)}
    />
  );

  const reExecuteFromFailureItem = (
    <MenuItem
      icon="sync_problem"
      text="Re-execute latest run from failure"
      onClick={() => onLaunch({type: 'from-failure'})}
      disabled={!canLaunchPipelineReexecution.enabled || !run || !canRunFromFailure(run)}
    />
  );

  return (
    <Popover
      onOpened={() => fetchIfPossible()}
      content={
        <Menu>
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
          {canLaunchPipelineReexecution.enabled ? (
            reExecuteAllItem
          ) : (
            <Tooltip content={canLaunchPipelineReexecution.disabledReason} display="block">
              {reExecuteAllItem}
            </Tooltip>
          )}
          {canLaunchPipelineReexecution.enabled ? (
            reExecuteFromFailureItem
          ) : (
            <Tooltip content={canLaunchPipelineReexecution.disabledReason} display="block">
              {reExecuteFromFailureItem}
            </Tooltip>
          )}
        </Menu>
      }
      position="bottom-left"
    >
      <Button icon={<Icon name="expand_more" />} />
    </Popover>
  );
};

const RUN_RE_EXECUTION_QUERY = graphql(`
  query RunReExecutionQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        ...RunFragment
      }
    }
  }
`);
