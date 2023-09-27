import {gql, useLazyQuery} from '@apollo/client';
import {Button, Icon, Menu, MenuItem, Popover, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {ReexecutionStrategy} from '../graphql/types';
import {canRunAllSteps, canRunFromFailure} from '../runs/RunActionButtons';
import {RUN_FRAGMENT} from '../runs/RunFragments';
import {RunTimeFragment} from '../runs/types/RunUtils.types';
import {useJobReexecution} from '../runs/useJobReExecution';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {RunReExecutionQuery, RunReExecutionQueryVariables} from './types/JobMenu.types';

interface Props {
  job: {isJob: boolean; name: string; runs: RunTimeFragment[]};
  repoAddress: RepoAddress;
}

/**
 * Lazily load more information about the last run for this job, then use that data to inform
 * whether re-execution is possible.
 */
export const JobMenu = (props: Props) => {
  const {job, repoAddress} = props;
  const lastRun = job.runs.length ? job.runs[0] : null;
  const {
    permissions: {canLaunchPipelineReexecution},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const [fetchHasExecutionPlan, {data}] = useLazyQuery<
    RunReExecutionQuery,
    RunReExecutionQueryVariables
  >(RUN_RE_EXECUTION_QUERY);

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data?.pipelineRunOrError : null;

  const fetchIfPossible = React.useCallback(() => {
    if (lastRun?.id) {
      fetchHasExecutionPlan({variables: {runId: lastRun.id}});
    }
  }, [lastRun, fetchHasExecutionPlan]);

  const onReexecute = useJobReexecution();

  const reExecuteAllItem = (
    <MenuItem
      icon="replay"
      text="Re-execute latest run"
      onClick={() => (run ? onReexecute(run, ReexecutionStrategy.ALL_STEPS) : undefined)}
      disabled={!canLaunchPipelineReexecution || !run || !canRunAllSteps(run)}
    />
  );

  const reExecuteFromFailureItem = (
    <MenuItem
      icon="sync_problem"
      text="Re-execute latest run from failure"
      onClick={() => (run ? onReexecute(run, ReexecutionStrategy.FROM_FAILURE) : undefined)}
      disabled={!canLaunchPipelineReexecution || !run || !canRunFromFailure(run)}
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
          {canLaunchPipelineReexecution ? (
            reExecuteAllItem
          ) : (
            <Tooltip content={disabledReasons.canLaunchPipelineReexecution} display="block">
              {reExecuteAllItem}
            </Tooltip>
          )}
          {canLaunchPipelineReexecution ? (
            reExecuteFromFailureItem
          ) : (
            <Tooltip content={disabledReasons.canLaunchPipelineReexecution} display="block">
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

const RUN_RE_EXECUTION_QUERY = gql`
  query RunReExecutionQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        parentPipelineSnapshotId
        ...RunFragment
      }
    }
  }

  ${RUN_FRAGMENT}
`;
