import {gql, useLazyQuery, useMutation} from '@apollo/client';
import * as qs from 'query-string';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {usePermissions} from '../app/Permissions';
import {ButtonWIP} from '../ui/Button';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';
import {IconWIP} from '../ui/Icon';
import {MenuDividerWIP, MenuItemWIP, MenuWIP} from '../ui/Menu';
import {Popover} from '../ui/Popover';
import {Tooltip} from '../ui/Tooltip';
import {isThisThingAJob} from '../workspace/WorkspaceContext';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';
import {workspacePipelinePath, workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

import {DeletionDialog} from './DeletionDialog';
import {RUN_FRAGMENT_FOR_REPOSITORY_MATCH} from './RunFragments';
import {doneStatuses} from './RunStatuses';
import {
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  RunsQueryRefetchContext,
  getReexecutionVariables,
  handleLaunchResult,
} from './RunUtils';
import {TerminationDialog} from './TerminationDialog';
import {LaunchPipelineReexecution} from './types/LaunchPipelineReexecution';
import {PipelineEnvironmentYamlQuery} from './types/PipelineEnvironmentYamlQuery';
import {RunTableRunFragment} from './types/RunTableRunFragment';

export const RunActionsMenu: React.FC<{
  run: RunTableRunFragment;
}> = React.memo(({run}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<'none' | 'terminate' | 'delete'>('none');

  const {basePath, rootServerURI} = React.useContext(AppContext);
  const {canTerminatePipelineExecution, canDeletePipelineRun} = usePermissions();

  const [reexecute] = useMutation<LaunchPipelineReexecution>(LAUNCH_PIPELINE_REEXECUTION_MUTATION, {
    onCompleted: refetch,
  });

  const [loadEnv, {called, loading, data}] = useLazyQuery<PipelineEnvironmentYamlQuery>(
    PIPELINE_ENVIRONMENT_YAML_QUERY,
    {
      variables: {runId: run.runId},
    },
  );

  const closeDialogs = () => {
    setVisibleDialog('none');
  };

  const onComplete = () => {
    refetch();
  };

  const pipelineRun =
    data?.pipelineRunOrError?.__typename === 'Run' ? data?.pipelineRunOrError : null;
  const runConfigYaml = pipelineRun?.runConfigYaml;

  const repoMatch = useRepositoryForRun(pipelineRun);
  const isFinished = doneStatuses.has(run.status);
  const isJob = !!(repoMatch && isThisThingAJob(repoMatch?.match, run.pipelineName));

  const playgroundPath = () => {
    const path = `/playground/setup?${qs.stringify({
      config: runConfigYaml,
      solidSelection: run.solidSelection,
    })}`;

    if (repoMatch) {
      return workspacePipelinePath({
        repoName: repoMatch.match.repository.name,
        repoLocation: repoMatch.match.repositoryLocation.name,
        pipelineName: run.pipelineName,
        isJob,
        path,
      });
    }

    return workspacePipelinePathGuessRepo(run.pipelineName, isJob, path);
  };

  const infoReady = called ? !loading : false;
  return (
    <>
      <Popover
        content={
          <MenuWIP>
            <MenuItemWIP
              text={loading ? 'Loading Configuration...' : 'View Configuration...'}
              disabled={!runConfigYaml}
              icon="open_in_new"
              onClick={() =>
                showCustomAlert({
                  title: 'Config',
                  body: <HighlightedCodeBlock value={runConfigYaml || ''} language="yaml" />,
                })
              }
            />
            <MenuDividerWIP />
            <>
              <Tooltip
                content={OPEN_PLAYGROUND_UNKNOWN}
                position="bottom"
                disabled={infoReady}
                targetTagName="div"
              >
                <MenuItemWIP
                  text="Open in Launchpad..."
                  disabled={!infoReady}
                  icon="edit"
                  href={playgroundPath()}
                />
              </Tooltip>
              <Tooltip
                content={
                  'Re-execute is unavailable because the pipeline is not present in the current workspace.'
                }
                position="bottom"
                disabled={infoReady && !!repoMatch}
                targetTagName="div"
              >
                <MenuItemWIP
                  text="Re-execute"
                  disabled={!infoReady || !repoMatch}
                  icon="refresh"
                  onClick={async () => {
                    if (repoMatch && runConfigYaml) {
                      const result = await reexecute({
                        variables: getReexecutionVariables({
                          run: {...run, runConfigYaml},
                          style: {type: 'all'},
                          repositoryLocationName: repoMatch.match.repositoryLocation.name,
                          repositoryName: repoMatch.match.repository.name,
                        }),
                      });
                      handleLaunchResult(basePath, run.pipelineName, result);
                    }
                  }}
                />
              </Tooltip>
              {isFinished || !canTerminatePipelineExecution ? null : (
                <MenuItemWIP
                  icon="cancel"
                  text="Terminate"
                  onClick={() => setVisibleDialog('terminate')}
                />
              )}
              <MenuDividerWIP />
            </>
            <MenuItemWIP
              text="Download Debug File"
              icon="download_for_offline"
              download
              href={`${rootServerURI}/download_debug/${run.runId}`}
            />
            {canDeletePipelineRun ? (
              <MenuItemWIP
                icon="delete"
                text="Delete"
                intent="danger"
                onClick={() => setVisibleDialog('delete')}
              />
            ) : null}
          </MenuWIP>
        }
        position="bottom-right"
        onOpening={() => {
          if (!called) {
            loadEnv();
          }
        }}
      >
        <ButtonWIP icon={<IconWIP name="expand_more" />} />
      </Popover>
      {canTerminatePipelineExecution ? (
        <TerminationDialog
          isOpen={visibleDialog === 'terminate'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
      {canDeletePipelineRun ? (
        <DeletionDialog
          isOpen={visibleDialog === 'delete'}
          onClose={closeDialogs}
          onComplete={onComplete}
          onTerminateInstead={() => setVisibleDialog('terminate')}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
    </>
  );
});

export const RunBulkActionsMenu: React.FC<{
  selected: RunTableRunFragment[];
  clearSelection: () => void;
}> = React.memo(({selected, clearSelection}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const {canTerminatePipelineExecution, canDeletePipelineRun} = usePermissions();
  const [visibleDialog, setVisibleDialog] = React.useState<'none' | 'terminate' | 'delete'>('none');

  if (!canTerminatePipelineExecution && !canDeletePipelineRun) {
    return null;
  }

  const unfinishedRuns = selected.filter((r) => !doneStatuses.has(r?.status));
  const unfinishedIDs = unfinishedRuns.map((r) => r.id);
  const unfinishedMap = unfinishedRuns.reduce(
    (accum, run) => ({...accum, [run.id]: run.canTerminate}),
    {},
  );

  const selectedIDs = selected.map((run) => run.runId);
  const deletionMap = selected.reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {});

  const closeDialogs = () => {
    setVisibleDialog('none');
  };

  const onComplete = () => {
    clearSelection();
    refetch();
  };

  return (
    <>
      <Popover
        content={
          <MenuWIP>
            {canTerminatePipelineExecution ? (
              <MenuItemWIP
                icon="cancel"
                text={`Terminate ${unfinishedIDs.length} ${
                  unfinishedIDs.length === 1 ? 'run' : 'runs'
                }`}
                disabled={unfinishedIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('terminate');
                }}
              />
            ) : null}
            {canDeletePipelineRun ? (
              <MenuItemWIP
                icon="delete"
                intent="danger"
                text={`Delete ${selectedIDs.length} ${selectedIDs.length === 1 ? 'run' : 'runs'}`}
                disabled={selectedIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('delete');
                }}
              />
            ) : null}
          </MenuWIP>
        }
        position="bottom-right"
      >
        <ButtonWIP disabled={selected.length === 0} rightIcon={<IconWIP name="expand_more" />}>
          Actions
        </ButtonWIP>
      </Popover>
      <TerminationDialog
        isOpen={visibleDialog === 'terminate'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={unfinishedMap}
      />
      <DeletionDialog
        isOpen={visibleDialog === 'delete'}
        onClose={closeDialogs}
        onComplete={onComplete}
        onTerminateInstead={() => setVisibleDialog('terminate')}
        selectedRuns={deletionMap}
      />
    </>
  );
});

const OPEN_PLAYGROUND_UNKNOWN =
  'Launchpad is unavailable because the pipeline is not present in the current repository.';

// Avoid fetching envYaml on load in Runs page. It is slow.
const PIPELINE_ENVIRONMENT_YAML_QUERY = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        pipeline {
          name
        }
        pipelineSnapshotId
        runConfigYaml
        ...RunFragmentForRepositoryMatch
      }
    }
  }
  ${RUN_FRAGMENT_FOR_REPOSITORY_MATCH}
`;
