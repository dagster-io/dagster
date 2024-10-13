import {
  Box,
  Button,
  Colors,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  JoinedButtons,
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Popover,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import {RunMetricsDialog} from 'shared/runs/RunMetricsDialog.oss';
import styled from 'styled-components';

import {DeletionDialog} from './DeletionDialog';
import {ReexecutionDialog} from './ReexecutionDialog';
import {RunConfigDialog} from './RunConfigDialog';
import {doneStatuses, failedStatuses} from './RunStatuses';
import {RunTags} from './RunTags';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunFilterToken} from './RunsFilterInput';
import {TerminationDialog} from './TerminationDialog';
import {
  PipelineEnvironmentQuery,
  PipelineEnvironmentQueryVariables,
  RunActionsMenuRunFragment,
} from './types/RunActionsMenu.types';
import {useJobAvailabilityErrorForRun} from './useJobAvailabilityErrorForRun';
import {useJobReexecution} from './useJobReExecution';
import {gql, useLazyQuery} from '../apollo-client';
import {AppContext} from '../app/AppContext';
import {showSharedToaster} from '../app/DomUtils';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {useCopyToClipboard} from '../app/browser';
import {ReexecutionStrategy} from '../graphql/types';
import {getPipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {AnchorButton} from '../ui/AnchorButton';
import {MenuLink} from '../ui/MenuLink';
import {isThisThingAJob} from '../workspace/WorkspaceContext/util';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';
import {workspacePipelineLinkForRun} from '../workspace/workspacePath';

interface Props {
  run: RunActionsMenuRunFragment;
  onAddTag?: (token: RunFilterToken) => void;
  anchorLabel?: React.ReactNode;
}

export const RunActionsMenu = React.memo(({run, onAddTag, anchorLabel}: Props) => {
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'config' | 'tags' | 'metrics'
  >('none');

  const {rootServerURI} = React.useContext(AppContext);

  const copyConfig = useCopyToClipboard();
  const onCopy = async () => {
    copyConfig(runConfigYaml || '');
    await showSharedToaster({
      intent: 'success',
      icon: 'copy_to_clipboard_done',
      message: 'Copied!',
    });
  };

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
  const runMetricsEnabled = run.hasRunMetricsEnabled;
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

  const jobLink = workspacePipelineLinkForRun({
    run,
    repositoryName: repoMatch?.match.repository.name,
    repositoryLocationName: repoMatch?.match.repositoryLocation.name,
    isJob,
  });

  return (
    <>
      <JoinedButtons>
        <AnchorButton to={`/runs/${run.id}`}>{anchorLabel ?? 'View run'}</AnchorButton>
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
                    icon="history"
                    text="View snapshot"
                    onClick={() => setVisibleDialog('tags')}
                  />
                </LinkNoUnderline>
              ) : null}
              <MenuDivider />
              <>
                <Tooltip
                  content={jobLink.disabledReason || OPEN_LAUNCHPAD_UNKNOWN}
                  position="left"
                  disabled={infoReady && !jobLink.disabledReason}
                  targetTagName="div"
                >
                  <MenuLink
                    text={jobLink.label}
                    disabled={!infoReady || !!jobLink.disabledReason}
                    icon={jobLink.icon}
                    to={jobLink.to}
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
                <MenuDivider />
              </>
              <MenuExternalLink
                text="Download debug file"
                icon="download_for_offline"
                download
                href={`${rootServerURI}/download_debug/${run.id}`}
              />
              {runMetricsEnabled && RunMetricsDialog ? (
                <MenuItem
                  tagName="button"
                  icon="asset_plot"
                  text="View container metrics"
                  intent="none"
                  onClick={() => setVisibleDialog('metrics')}
                />
              ) : null}
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
      {runMetricsEnabled && RunMetricsDialog ? (
        <RunMetricsDialog
          runId={run.id}
          isOpen={visibleDialog === 'metrics'}
          onClose={closeDialogs}
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
      <RunConfigDialog
        isOpen={visibleDialog === 'config'}
        onClose={closeDialogs}
        copyConfig={onCopy}
        mode={run.mode}
        runConfigYaml={runConfigYaml || ''}
        isJob={isJob}
      />
    </>
  );
});

interface RunBulkActionsMenuProps {
  selected: RunActionsMenuRunFragment[];
  clearSelection: () => void;
  notice?: React.ReactNode;
}

export const RunBulkActionsMenu = React.memo((props: RunBulkActionsMenuProps) => {
  const {selected, clearSelection, notice} = props;
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
    (accum, run) => {
      accum[run.id] = run.canTerminate;
      return accum;
    },
    {} as Record<string, boolean>,
  );

  const deleteableIDs = selected.map((run) => run.id);
  const deletionMap = selected.reduce(
    (accum, run) => {
      accum[run.id] = run.canTerminate;
      return accum;
    },
    {} as Record<string, boolean>,
  );

  const reexecuteFromFailureRuns = selected.filter(
    (r) => failedStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecuteFromFailureMap = reexecuteFromFailureRuns.reduce(
    (accum, run) => {
      accum[run.id] = run.id;
      return accum;
    },
    {} as Record<string, string>,
  );

  const reexecutableRuns = selected.filter(
    (r) => doneStatuses.has(r?.status) && r.hasReExecutePermission,
  );
  const reexecutableMap = reexecutableRuns.reduce(
    (accum, run) => {
      accum[run.id] = run.id;
      return accum;
    },
    {} as Record<string, string>,
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
            {notice}
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

export const RUN_ACTIONS_MENU_RUN_FRAGMENT = gql`
  fragment RunActionsMenuRunFragment on Run {
    id
    assetSelection {
      ... on AssetKey {
        path
      }
    }
    assetCheckSelection {
      name
      assetKey {
        path
      }
    }
    tags {
      key
      value
    }
    hasReExecutePermission
    hasTerminatePermission
    hasDeletePermission
    canTerminate
    mode
    status
    pipelineName
    pipelineSnapshotId
    repositoryOrigin {
      repositoryName
      repositoryLocationName
    }
    hasRunMetricsEnabled
  }
`;

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
        hasRunMetricsEnabled
      }
    }
  }
`;

const SlashShortcut = styled.div`
  border-radius: 4px;
  padding: 0px 6px;
  background: ${Colors.backgroundLight()};
  color: ${Colors.textLight()};
`;

const LinkNoUnderline = styled(Link)`
  text-decoration: none !important;
`;
