import {gql, useLazyQuery} from '@apollo/client';
import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';
import {ReexecutionStrategy} from '../graphql/types';
import {canRunAllSteps, canRunFromFailure} from '../runs/RunActionButtons';
import {RunTimeFragment} from '../runs/types/RunUtils.types';
import {useJobReexecution} from '../runs/useJobReExecution';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

import {RunReExecutionQuery, RunReExecutionQueryVariables} from './types/JobMenu.types';

interface Props {
  job: {isJob: boolean; name: string; runs: RunTimeFragment[]};
  repoAddress: RepoAddress;
  isAssetJob: boolean | 'loading';
}

/**
 * Lazily load more information about the last run for this job, then use that data to inform
 * whether re-execution is possible.
 */
export const JobMenu = (props: Props) => {
  const {job, isAssetJob, repoAddress} = props;
  const lastRun = job.runs.length ? job.runs[0] : null;
  const pipelineSelector = {
    pipelineName: job.name,
    repositoryName: repoAddress.name,
    repositoryLocationName: repoAddress.location,
  };

  const materialize = useMaterializationAction(job.name);
  const onReexecute = useJobReexecution();

  const {
    permissions: {canLaunchPipelineReexecution, canLaunchPipelineExecution},
    disabledReasons,
  } = usePermissionsForLocation(repoAddress.location);

  const [fetchHasExecutionPlan, {data}] = useLazyQuery<
    RunReExecutionQuery,
    RunReExecutionQueryVariables
  >(RUN_RE_EXECUTION_QUERY);

  const fetchIfPossible = React.useCallback(() => {
    if (lastRun?.id) {
      fetchHasExecutionPlan({variables: {runId: lastRun.id}});
    }
  }, [lastRun, fetchHasExecutionPlan]);

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data?.pipelineRunOrError : null;
  const executeItem =
    isAssetJob === 'loading' ? (
      <MenuItem icon="execute" text="Loading..." disabled={true} />
    ) : isAssetJob === true ? (
      <MenuItem
        icon={materialize.loading ? <Spinner purpose="caption-text" /> : 'execute'}
        text="Launch new run"
        disabled={!canLaunchPipelineExecution}
        onClick={(e) => materialize.onClick(pipelineSelector, e)}
      />
    ) : (
      <MenuLink
        icon="execute"
        text="Launch new run"
        disabled={!canLaunchPipelineExecution}
        to={workspacePipelinePath({
          repoName: repoAddress.name,
          repoLocation: repoAddress.location,
          pipelineName: job.name,
          isJob: job.isJob,
          path: '/playground',
        })}
      />
    );

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
    <>
      {materialize.launchpadElement}
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
            {canLaunchPipelineExecution ? (
              executeItem
            ) : (
              <Tooltip content={disabledReasons.canLaunchPipelineExecution} display="block">
                {executeItem}
              </Tooltip>
            )}
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
    </>
  );
};

const RUN_RE_EXECUTION_QUERY = gql`
  query RunReExecutionQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        status
        pipelineName
        executionPlan {
          artifactsPersisted
          ...ExecutionPlanToGraphFragment
        }
      }
    }
  }
  ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
`;
