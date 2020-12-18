import {gql, useLazyQuery, useMutation} from '@apollo/client';
import {
  Button,
  Intent,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  Position,
  Tooltip,
} from '@blueprintjs/core';
import * as qs from 'query-string';
import * as React from 'react';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {SharedToaster, ROOT_SERVER_URI} from 'src/DomUtils';
import {HighlightedCodeBlock} from 'src/HighlightedCodeBlock';
import {DeletionDialog} from 'src/runs/DeletionDialog';
import {REEXECUTE_PIPELINE_UNKNOWN} from 'src/runs/RunActionButtons';
import {RUN_FRAGMENT_FOR_REPOSITORY_MATCH} from 'src/runs/RunFragments';
import {doneStatuses} from 'src/runs/RunStatuses';
import {
  CANCEL_MUTATION,
  DELETE_MUTATION,
  LAUNCH_PIPELINE_REEXECUTION_MUTATION,
  RunsQueryRefetchContext,
  getReexecutionVariables,
  handleLaunchResult,
} from 'src/runs/RunUtils';
import {TerminationDialog} from 'src/runs/TerminationDialog';
import {Cancel} from 'src/runs/types/Cancel';
import {Delete} from 'src/runs/types/Delete';
import {LaunchPipelineReexecution} from 'src/runs/types/LaunchPipelineReexecution';
import {PipelineEnvironmentYamlQuery} from 'src/runs/types/PipelineEnvironmentYamlQuery';
import {RunActionMenuFragment} from 'src/runs/types/RunActionMenuFragment';
import {RunTableRunFragment} from 'src/runs/types/RunTableRunFragment';
import {useRepositoryForRun} from 'src/workspace/useRepositoryForRun';

export const RunActionsMenu: React.FC<{
  run: RunTableRunFragment | RunActionMenuFragment;
}> = React.memo(({run}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);

  const [reexecute] = useMutation<LaunchPipelineReexecution>(LAUNCH_PIPELINE_REEXECUTION_MUTATION, {
    onCompleted: refetch,
  });
  const [cancel] = useMutation<Cancel>(CANCEL_MUTATION, {onCompleted: refetch});
  const [destroy] = useMutation<Delete>(DELETE_MUTATION, {onCompleted: refetch});
  const [loadEnv, {called, loading, data}] = useLazyQuery<PipelineEnvironmentYamlQuery>(
    PIPELINE_ENVIRONMENT_YAML_QUERY,
    {
      variables: {runId: run.runId},
    },
  );

  const pipelineRun =
    data?.pipelineRunOrError?.__typename === 'PipelineRun' ? data?.pipelineRunOrError : null;
  const runConfigYaml = pipelineRun?.runConfigYaml;

  const repoMatch = useRepositoryForRun(pipelineRun);

  const infoReady = called ? !loading : false;
  return (
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
                href={`/workspace/pipelines/${run.pipelineName}/playground/setup?${qs.stringify({
                  mode: run.mode,
                  config: runConfigYaml,
                  solidSelection: run.solidSelection,
                })}`}
              />
            </Tooltip>
            <Tooltip
              content={REEXECUTE_PIPELINE_UNKNOWN}
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
                    handleLaunchResult(run.pipelineName, result, {openInNewWindow: true});
                  }
                }}
              />
            </Tooltip>
            <MenuItem
              text="Cancel"
              icon="stop"
              disabled={!run.canTerminate}
              onClick={async () => {
                const result = await cancel({variables: {runId: run.runId}});
                showToastFor(
                  result.data?.terminatePipelineExecution,
                  `Run ${run.runId} canceled.`,
                  `Something went wrong when trying to cancel Run ${run.runId}`,
                );
              }}
            />
            <MenuDivider />
          </>
          <MenuItem
            text="Download Debug File"
            icon="download"
            download
            href={`${ROOT_SERVER_URI}/download_debug/${run.runId}`}
          />
          <MenuItem
            text="Delete"
            icon="trash"
            disabled={run.canTerminate}
            onClick={async () => {
              const result = await destroy({variables: {runId: run.runId}});
              showToastFor(
                result.data?.deletePipelineRun,
                `Run ${run.runId} deleted.`,
                `Something went wrong when trying to delete Run ${run.runId}`,
              );
            }}
          />
        </Menu>
      }
      position={'bottom'}
      onOpening={() => {
        if (!called) {
          loadEnv();
        }
      }}
    >
      <Button minimal={true} icon="more" />
    </Popover>
  );
});

export const RunBulkActionsMenu: React.FunctionComponent<{
  selected: RunTableRunFragment[];
  onChangeSelection: (runs: RunTableRunFragment[]) => void;
}> = React.memo(({selected, onChangeSelection}) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<'none' | 'terminate' | 'delete'>('none');

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
    onChangeSelection([]);
    refetch();
  };

  return (
    <>
      <Popover
        content={
          <Menu>
            <MenuItem
              icon="stop"
              text={`Cancel ${unfinishedIDs.length} ${unfinishedIDs.length === 1 ? 'run' : 'runs'}`}
              disabled={unfinishedIDs.length === 0}
              onClick={() => {
                setVisibleDialog('terminate');
              }}
            />
            <MenuItem
              icon="trash"
              text={`Delete ${selectedIDs.length} ${selectedIDs.length === 1 ? 'run' : 'runs'}`}
              disabled={selectedIDs.length === 0}
              onClick={() => {
                setVisibleDialog('delete');
              }}
            />
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

function showToastFor(
  possibleError: {__typename: string; message?: string} | null | undefined,
  successMessage: string,
  genericErrorMessage: string,
) {
  if (!possibleError) {
    SharedToaster.show({
      message: genericErrorMessage,
      icon: 'error',
      intent: Intent.DANGER,
    });
  } else if ('message' in possibleError) {
    SharedToaster.show({
      message: possibleError.message,
      icon: 'error',
      intent: Intent.DANGER,
    });
  } else {
    SharedToaster.show({
      message: successMessage,
      icon: 'confirm',
      intent: Intent.SUCCESS,
    });
  }
}

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
