import {gql, useLazyQuery, useMutation} from '@apollo/client';
import {Button, Menu, MenuDivider, MenuItem, Popover, Position, Tooltip} from '@blueprintjs/core';
import * as qs from 'query-string';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {usePermissions} from '../app/Permissions';
import {HighlightedCodeBlock} from '../ui/HighlightedCodeBlock';
import {useRepositoryForRun} from '../workspace/useRepositoryForRun';
import {workspacePipelinePathGuessRepo} from '../workspace/workspacePath';

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
    data?.pipelineRunOrError?.__typename === 'PipelineRun' ? data?.pipelineRunOrError : null;
  const runConfigYaml = pipelineRun?.runConfigYaml;

  const repoMatch = useRepositoryForRun(pipelineRun);
  const isFinished = doneStatuses.has(run.status);

  const infoReady = called ? !loading : false;
  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              text={loading ? 'Loading Configuration...' : 'View Configuration...'}
              disabled={!runConfigYaml}
              icon="share"
              onClick={() =>
                showCustomAlert({
                  title: 'Config',
                  body: <HighlightedCodeBlock value={runConfigYaml || ''} language="yaml" />,
                })
              }
            />
            <MenuDivider />
            <>
              <Tooltip
                content={OPEN_PLAYGROUND_UNKNOWN}
                position={Position.BOTTOM}
                disabled={infoReady}
                wrapperTagName="div"
                targetTagName="div"
              >
                <MenuItem
                  text="Open in Playground..."
                  disabled={!infoReady}
                  icon="edit"
                  target="_blank"
                  href={workspacePipelinePathGuessRepo(
                    run.pipelineName,
                    run.mode,
                    `/playground/setup?${qs.stringify({
                      config: runConfigYaml,
                      solidSelection: run.solidSelection,
                    })}`,
                  )}
                />
              </Tooltip>
              <Tooltip
                content={
                  'Re-execute is unavailable because the pipeline is not present in the current workspace.'
                }
                position={Position.BOTTOM}
                disabled={infoReady && !!repoMatch}
                wrapperTagName="div"
                targetTagName="div"
              >
                <MenuItem
                  text="Re-execute"
                  disabled={!infoReady || !repoMatch}
                  icon="repeat"
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
                <MenuItem
                  icon="stop"
                  text="Terminate"
                  onClick={() => setVisibleDialog('terminate')}
                />
              )}
              <MenuDivider />
            </>
            <MenuItem
              text="Download Debug File"
              icon="download"
              download
              href={`${rootServerURI}/download_debug/${run.runId}`}
            />
            {canDeletePipelineRun ? (
              <MenuItem icon="trash" text="Delete" onClick={() => setVisibleDialog('delete')} />
            ) : null}
          </Menu>
        }
        position={'bottom'}
        onOpening={() => {
          if (!called) {
            loadEnv();
          }
        }}
      >
        <Button minimal={true} icon="more" style={{position: 'relative', top: '-6px'}} />
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
          <Menu>
            {canTerminatePipelineExecution ? (
              <MenuItem
                icon="stop"
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
              <MenuItem
                icon="trash"
                text={`Delete ${selectedIDs.length} ${selectedIDs.length === 1 ? 'run' : 'runs'}`}
                disabled={selectedIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('delete');
                }}
              />
            ) : null}
          </Menu>
        }
        position={'bottom'}
      >
        <Button disabled={selected.length === 0} text="Actions" rightIcon="caret-down" small />
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
  'Playground is unavailable because the pipeline is not present in the current repository.';

// Avoid fetching envYaml on load in Runs page. It is slow.
const PIPELINE_ENVIRONMENT_YAML_QUERY = gql`
  query PipelineEnvironmentYamlQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on PipelineRun {
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
