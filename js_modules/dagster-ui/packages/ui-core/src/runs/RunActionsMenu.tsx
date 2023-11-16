import {gql, useLazyQuery} from '@apollo/client';
import {
  Button,
  Icon,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Menu,
  Popover,
  Tooltip,
  DialogFooter,
  Dialog,
  JoinedButtons,
  DialogBody,
  Box,
  StyledRawCodeMirror,
  colorBackgroundLight,
  colorTextLight,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AppContext} from '../app/AppContext';
import {showSharedToaster} from '../app/DomUtils';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {useCopyToClipboard} from '../app/browser';
import {ReexecutionStrategy} from '../graphql/types';
import {NO_LAUNCH_PERMISSION_MESSAGE} from '../launchpad/LaunchRootExecutionButton';
import {getPipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {AnchorButton} from '../ui/AnchorButton';
import {MenuLink} from '../ui/MenuLink';
import {isThisThingAJob} from '../workspace/WorkspaceContext';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';
import {workspacePathFromRunDetails} from '../workspace/workspacePath';

import {DeletionDialog} from './DeletionDialog';
import {ReexecutionDialog} from './ReexecutionDialog';
import {doneStatuses, failedStatuses} from './RunStatuses';
import {RunTags} from './RunTags';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {TerminationDialog} from './TerminationDialog';
import {
  PipelineEnvironmentQuery,
  PipelineEnvironmentQueryVariables,
} from './types/RunActionsMenu.types';
import {RunTableRunFragment} from './types/RunTable.types';
import {useJobAvailabilityErrorForRun} from './useJobAvailabilityErrorForRun';
import {useJobReexecution} from './useJobReExecution';

interface Props {
  run: RunTableRunFragment;
  additionalActionsForRun?: (run: RunTableRunFragment) => React.ReactNode[];
  onAddTag?: (token: RunFilterToken) => void;
}

export const RunActionsMenu = React.memo(({run, onAddTag, additionalActionsForRun}: Props) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'config' | 'tags'
  >('none');

  const {rootServerURI} = React.useContext(AppContext);

  const copyConfig = useCopyToClipboard();
  const reexecute = useJobReexecution({onCompleted: refetch});

  const [loadEnv, {called, loading, data}] = useLazyQuery<
    PipelineEnvironmentQuery,
    PipelineEnvironmentQueryVariables
  >(PIPELINE_ENVIRONMENT_QUERY, {
    variables: {runId: run.id},
  });

  const closeDialogs = () => {
    setVisibleDialog('none');
  };

  const onComplete = () => {
    refetch();
  };

  const pipelineRun =
    data?.pipelineRunOrError?.__typename === 'Run' ? data?.pipelineRunOrError : null;
  const runConfigYaml = pipelineRun?.runConfigYaml;

  const repoMatch = useRepositoryForRunWithParentSnapshot(pipelineRun);
  const jobError = useJobAvailabilityErrorForRun({
    ...run,
    parentPipelineSnapshotId: pipelineRun?.parentPipelineSnapshotId,
  });

  const isFinished = doneStatuses.has(run.status);
  const isJob = !!(repoMatch && isThisThingAJob(repoMatch?.match, run.pipelineName));

  const infoReady = called ? !loading : false;

  const reexecutionDisabledState = React.useMemo(() => {
    if (!run.hasReExecutePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (jobError) {
      return {disabled: jobError.disabled, message: jobError.tooltip};
    }
    if (!infoReady) {
      return {disabled: true};
    }
    return {disabled: false};
  }, [run.hasReExecutePermission, jobError, infoReady]);

  return (
    <>
      <JoinedButtons>
        <AnchorButton to={`/runs/${run.id}`}>View run</AnchorButton>
        <Popover
          content={
            <Menu>
              <MenuItem
                tagName="button"
                style={{minWidth: 200}}
                text={loading ? 'Loading configuration...' : 'View configuration...'}
                disabled={!runConfigYaml}
                icon="open_in_new"
                onClick={() => setVisibleDialog('config')}
              />
              <MenuItem
                tagName="button"
                text={
                  <div style={{display: 'contents'}}>
                    View all tags
                    <Box
                      flex={{
                        justifyContent: 'center',
                        alignItems: 'center',
                        display: 'inline-flex',
                      }}
                      padding={{horizontal: 8}}
                    >
                      <SlashShortcut>t</SlashShortcut>
                    </Box>
                  </div>
                }
                icon="tag"
                onClick={() => setVisibleDialog('tags')}
              />

              {run.pipelineSnapshotId ? (
                <LinkNoUnderline
                  to={getPipelineSnapshotLink(run.pipelineName, run.pipelineSnapshotId)}
                >
                  <MenuItem
                    tagName="button"
                    icon="job"
                    text="View snapshot"
                    onClick={() => setVisibleDialog('tags')}
                  />
                </LinkNoUnderline>
              ) : null}
              <MenuDivider />
              <>
                <Tooltip
                  content={
                    run.hasReExecutePermission
                      ? OPEN_LAUNCHPAD_UNKNOWN
                      : NO_LAUNCH_PERMISSION_MESSAGE
                  }
                  position="left"
                  disabled={infoReady && run.hasReExecutePermission}
                  targetTagName="div"
                >
                  <MenuLink
                    text="Open in Launchpad..."
                    disabled={!infoReady || !run.hasReExecutePermission}
                    icon="edit"
                    to={workspacePathFromRunDetails({
                      id: run.id,
                      pipelineName: run.pipelineName,
                      repositoryName: repoMatch?.match.repository.name,
                      repositoryLocationName: repoMatch?.match.repositoryLocation.name,
                      isJob,
                    })}
                  />
                </Tooltip>
                <Tooltip
                  content={reexecutionDisabledState.message || ''}
                  position="left"
                  canShow={reexecutionDisabledState.disabled}
                  targetTagName="div"
                >
                  <MenuItem
                    tagName="button"
                    text="Re-execute"
                    disabled={reexecutionDisabledState.disabled}
                    icon="refresh"
                    onClick={async () => {
                      await reexecute(run, ReexecutionStrategy.ALL_STEPS);
                    }}
                  />
                </Tooltip>
                {isFinished || !run.hasTerminatePermission ? null : (
                  <MenuItem
                    tagName="button"
                    icon="cancel"
                    text="Terminate"
                    onClick={() => setVisibleDialog('terminate')}
                  />
                )}
                {additionalActionsForRun?.(run)}
                <MenuDivider />
              </>
              <MenuExternalLink
                text="Download debug file"
                icon="download_for_offline"
                download
                href={`${rootServerURI}/download_debug/${run.id}`}
              />
              {run.hasDeletePermission ? (
                <MenuItem
                  tagName="button"
                  icon="delete"
                  text="Delete"
                  intent="danger"
                  onClick={() => setVisibleDialog('delete')}
                />
              ) : null}
            </Menu>
          }
          position="bottom-right"
          onOpening={() => {
            if (!called) {
              loadEnv();
            }
          }}
        >
          <Button icon={<Icon name="expand_more" />} />
        </Popover>
      </JoinedButtons>
      {run.hasTerminatePermission ? (
        <TerminationDialog
          isOpen={visibleDialog === 'terminate'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
      {run.hasDeletePermission ? (
        <DeletionDialog
          isOpen={visibleDialog === 'delete'}
          onClose={closeDialogs}
          onComplete={onComplete}
          onTerminateInstead={() => setVisibleDialog('terminate')}
          selectedRuns={{[run.id]: run.canTerminate}}
        />
      ) : null}
      <Dialog
        isOpen={visibleDialog === 'tags'}
        title="Tags"
        canOutsideClickClose
        canEscapeKeyClose
        onClose={closeDialogs}
      >
        <DialogBody>
          <RunTags
            tags={run.tags}
            mode={isJob ? (run.mode !== 'default' ? run.mode : null) : run.mode}
            onAddTag={onAddTag}
          />
        </DialogBody>
        <DialogFooter topBorder>
          <Button intent="primary" onClick={closeDialogs}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
      <Dialog
        isOpen={visibleDialog === 'config'}
        title="Config"
        canOutsideClickClose
        canEscapeKeyClose
        onClose={closeDialogs}
      >
        <StyledRawCodeMirror
          value={runConfigYaml || ''}
          options={{readOnly: true, lineNumbers: true, mode: 'yaml'}}
        />
        <DialogFooter topBorder>
          <Button
            intent="none"
            onClick={async () => {
              copyConfig(runConfigYaml || '');
              await showSharedToaster({
                intent: 'success',
                icon: 'copy_to_clipboard_done',
                message: 'Copied!',
              });
            }}
          >
            Copy config
          </Button>
          <Button intent="primary" onClick={closeDialogs}>
            OK
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
});

interface RunBulkActionsMenuProps {
  selected: RunTableRunFragment[];
  clearSelection: () => void;
}

export const RunBulkActionsMenu = React.memo((props: RunBulkActionsMenuProps) => {
  const {selected, clearSelection} = props;
  const {refetch} = React.useContext(RunsQueryRefetchContext);

  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'reexecute-from-failure' | 'reexecute'
  >('none');

  const canTerminateAny = React.useMemo(() => {
    return selected.some((run) => run.hasTerminatePermission);
  }, [selected]);

  const canDeleteAny = React.useMemo(() => {
    return selected.some((run) => run.hasTerminatePermission);
  }, [selected]);

  const canReexecuteAny = React.useMemo(() => {
    return selected.some((run) => run.hasReExecutePermission);
  }, [selected]);

  const disabled = !canTerminateAny && !canDeleteAny;

  const terminatableRuns = selected.filter(
    (r) => !doneStatuses.has(r?.status) && r.hasTerminatePermission,
  );
  const terminateableIDs = terminatableRuns.map((r) => r.id);
  const terminateableMap = terminatableRuns.reduce(
    (accum, run) => ({...accum, [run.id]: run.canTerminate}),
    {},
  );

  const deleteableIDs = selected.map((run) => run.id);
  const deletionMap = selected.reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {});

  const reexecuteFromFailureRuns = selected.filter(
    (r) => failedStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecuteFromFailureMap = reexecuteFromFailureRuns.reduce(
    (accum, run) => ({...accum, [run.id]: run.id}),
    {},
  );

  const reexecutableRuns = selected.filter(
    (r) => doneStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecutableMap = reexecutableRuns.reduce(
    (accum, run) => ({...accum, [run.id]: run.id}),
    {},
  );

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
        disabled={disabled || selected.length === 0}
        content={
          <Menu>
            {canTerminateAny ? (
              <MenuItem
                icon="cancel"
                text={`Terminate ${terminateableIDs.length} ${
                  terminateableIDs.length === 1 ? 'run' : 'runs'
                }`}
                disabled={terminateableIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('terminate');
                }}
              />
            ) : null}
            {canDeleteAny ? (
              <MenuItem
                icon="delete"
                intent="danger"
                text={`Delete ${deleteableIDs.length} ${
                  deleteableIDs.length === 1 ? 'run' : 'runs'
                }`}
                disabled={deleteableIDs.length === 0}
                onClick={() => {
                  setVisibleDialog('delete');
                }}
              />
            ) : null}
            {canReexecuteAny ? (
              <>
                <MenuItem
                  icon="refresh"
                  text={`Re-execute ${reexecutableRuns.length} ${
                    reexecutableRuns.length === 1 ? 'run' : 'runs'
                  }`}
                  disabled={reexecutableRuns.length === 0}
                  onClick={() => {
                    setVisibleDialog('reexecute');
                  }}
                />
                <MenuItem
                  icon="refresh"
                  text={`Re-execute ${reexecuteFromFailureRuns.length} ${
                    reexecuteFromFailureRuns.length === 1 ? 'run' : 'runs'
                  } from failure`}
                  disabled={reexecuteFromFailureRuns.length === 0}
                  onClick={() => {
                    setVisibleDialog('reexecute-from-failure');
                  }}
                />
              </>
            ) : null}
          </Menu>
        }
        position="bottom-right"
      >
        <Button
          disabled={disabled || selected.length === 0}
          rightIcon={<Icon name="expand_more" />}
          intent="primary"
        >
          Actions
        </Button>
      </Popover>
      <TerminationDialog
        isOpen={visibleDialog === 'terminate'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={terminateableMap}
      />
      <DeletionDialog
        isOpen={visibleDialog === 'delete'}
        onClose={closeDialogs}
        onComplete={onComplete}
        onTerminateInstead={() => setVisibleDialog('terminate')}
        selectedRuns={deletionMap}
      />
      <ReexecutionDialog
        isOpen={visibleDialog === 'reexecute-from-failure'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={reexecuteFromFailureMap}
        reexecutionStrategy={ReexecutionStrategy.FROM_FAILURE}
      />
      <ReexecutionDialog
        isOpen={visibleDialog === 'reexecute'}
        onClose={closeDialogs}
        onComplete={onComplete}
        selectedRuns={reexecutableMap}
        reexecutionStrategy={ReexecutionStrategy.ALL_STEPS}
      />
    </>
  );
});

const OPEN_LAUNCHPAD_UNKNOWN =
  'Launchpad is unavailable because the pipeline is not present in the current repository.';

// Avoid fetching envYaml and parentPipelineSnapshotId on load in Runs page, they're slow.
export const PIPELINE_ENVIRONMENT_QUERY = gql`
  query PipelineEnvironmentQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        pipelineName
        pipelineSnapshotId
        runConfigYaml
        pipelineName
        parentPipelineSnapshotId
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
      }
    }
  }
`;

const SlashShortcut = styled.div`
  border-radius: 4px;
  padding: 0px 6px;
  background: ${colorBackgroundLight()};
  color: ${colorTextLight()};
`;

const LinkNoUnderline = styled(Link)`
  text-decoration: none !important;
`;
