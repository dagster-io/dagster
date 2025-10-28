import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useCallback} from 'react';

import {gql, useLazyQuery} from '../apollo-client';
import {RunReExecutionQuery, RunReExecutionQueryVariables} from './types/JobMenu.types';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {useLazyJobPermissions} from '../app/useJobPermissions';
import {useMaterializationAction} from '../assets/LaunchAssetExecutionButton';
import {EXECUTION_PLAN_TO_GRAPH_FRAGMENT} from '../gantt/toGraphQueryItems';
import {ReexecutionStrategy} from '../graphql/types';
import {canRunAllSteps, canRunFromFailure} from '../runs/RunActionButtons';
import {useJobReexecution} from '../runs/useJobReExecution';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePipelinePath} from '../workspace/workspacePath';

interface Props {
  job: {isJob: boolean; name: string; runs: {id: string}[]};
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
  const reexecute = useJobReexecution();

  const [fetchHasJobPermissions, {hasLaunchExecutionPermission, hasLaunchReexecutionPermission}] =
    useLazyJobPermissions(pipelineSelector, repoAddress.location);
  const [fetchHasExecutionPlan, queryResult] = useLazyQuery<
    RunReExecutionQuery,
    RunReExecutionQueryVariables
  >(RUN_RE_EXECUTION_QUERY);

  const {data} = queryResult;

  const fetchIfPossible = useCallback(() => {
    if (lastRun?.id) {
      fetchHasExecutionPlan({variables: {runId: lastRun.id}});
    }
    fetchHasJobPermissions();
  }, [lastRun, fetchHasExecutionPlan, fetchHasJobPermissions]);

  const run = data?.pipelineRunOrError.__typename === 'Run' ? data?.pipelineRunOrError : null;
  const executeItem =
    isAssetJob === 'loading' ? (
      <MenuItem icon="execute" text="Loading..." disabled={true} />
    ) : isAssetJob === true ? (
      <MenuItem
        icon={materialize.loading ? <Spinner purpose="caption-text" /> : 'execute'}
        text="Launch new run"
        disabled={!hasLaunchExecutionPermission}
        onClick={(e) => materialize.onClick(pipelineSelector, e)}
      />
    ) : (
      <MenuLink
        icon="execute"
        text="Launch new run"
        disabled={!hasLaunchExecutionPermission}
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
      disabled={!hasLaunchReexecutionPermission || !run || !canRunAllSteps(run)}
      onClick={(e) =>
        run ? reexecute.onClick(run, ReexecutionStrategy.ALL_STEPS, e.shiftKey) : undefined
      }
    />
  );

  const reExecuteFromFailureItem = (
    <MenuItem
      icon="sync_problem"
      text="Re-execute latest run from failure"
      disabled={!hasLaunchReexecutionPermission || !run || !canRunFromFailure(run)}
      onClick={(e) =>
        run ? reexecute.onClick(run, ReexecutionStrategy.FROM_FAILURE, e.shiftKey) : undefined
      }
    />
  );

  return (
    <>
      {materialize.launchpadElement}
      {reexecute.launchpadElement}
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
            {hasLaunchExecutionPermission ? (
              executeItem
            ) : (
              <Tooltip content={DEFAULT_DISABLED_REASON} display="block">
                {executeItem}
              </Tooltip>
            )}
            {hasLaunchReexecutionPermission ? (
              reExecuteAllItem
            ) : (
              <Tooltip content={DEFAULT_DISABLED_REASON} display="block">
                {reExecuteAllItem}
              </Tooltip>
            )}
            {hasLaunchReexecutionPermission ? (
              reExecuteFromFailureItem
            ) : (
              <Tooltip content={DEFAULT_DISABLED_REASON} display="block">
                {reExecuteFromFailureItem}
              </Tooltip>
            )}
          </Menu>
        }
        position="bottom-left"
      >
        <Button icon={<Icon name="more_horiz" />} intent="none" />
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
        tags {
          key
          value
        }
        executionPlan {
          artifactsPersisted
          assetKeys {
            path
          }
          ...ExecutionPlanToGraphFragment
        }
      }
    }
  }
  ${EXECUTION_PLAN_TO_GRAPH_FRAGMENT}
`;
