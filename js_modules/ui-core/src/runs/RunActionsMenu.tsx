import {
  Box,
  Button,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  IconName,
  JoinedButtons,
  Menu,
  MenuDivider,
  MenuExternalLink,
  MenuItem,
  Popover,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import {AISummaryForRunMenuItem} from '@shared/runs/AISummaryForRunMenuItem';
import {CreateIssueForRunDialog} from '@shared/runs/CreateIssueForRunDialog';
import {RunMetricsDialog} from '@shared/runs/RunMetricsDialog';
import {useCanCreateIssueForRun} from '@shared/runs/useCanCreateIssueForRun';
import uniq from 'lodash/uniq';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {DeletionDialog} from './DeletionDialog';
import {ReexecutionDialog} from './ReexecutionDialog';
import {RunConfigDialog} from './RunConfigDialog';
import {doneStatuses, failedStatuses} from './RunStatuses';
import {RunTags, tagsAsYamlString} from './RunTags';
import {RunsQueryRefetchContext} from './RunUtils';
import {RunFilterToken} from './RunsFilterUtils';
import {TerminationDialog} from './TerminationDialog';
import {
  PipelineEnvironmentQuery,
  PipelineEnvironmentQueryVariables,
} from './types/RunActionsMenu.types';
import {useJobAvailabilityErrorForRun} from './useJobAvailabilityErrorForRun';
import {useJobReexecution} from './useJobReExecution';
import {gql, useLazyQuery} from '../apollo-client';
import {DagsterTag} from './RunTag';
import {AppContext} from '../app/AppContext';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {ReexecutionStrategy} from '../graphql/types';
import {useMenuPopover} from '../hooks/useMenuPopover';
import {getPipelineSnapshotLink} from '../pipelines/PipelinePathUtils';
import {AnchorButton} from '../ui/AnchorButton';
import {CopyButton} from '../ui/CopyButton';
import {MenuLink} from '../ui/MenuLink';
import {numberFormatter} from '../ui/formatters';
import {isThisThingAJob} from '../workspace/WorkspaceContext/util';
import {useRepositoryForRunWithParentSnapshot} from '../workspace/useRepositoryForRun';
import {OPEN_LAUNCHPAD_UNKNOWN, workspacePipelineLinkForRun} from '../workspace/workspacePath';
import styles from './css/RunActionsMenu.module.css';
import {RunActionsMenuRunFragment} from './types/RunActionsMenuRunFragment.types';

interface Props {
  run: RunActionsMenuRunFragment;
  onAddTag?: (token: RunFilterToken) => void;
  anchorLabel?: React.ReactNode;
}

export const RunActionsMenu = React.memo(({run, onAddTag, anchorLabel}: Props) => {
  const canCreateIssue = useCanCreateIssueForRun(run.status);
  const {refetch} = React.useContext(RunsQueryRefetchContext);
  const [visibleDialog, setVisibleDialog] = React.useState<
    'none' | 'terminate' | 'delete' | 'config' | 'tags' | 'metrics' | 'create-issue'
  >('none');

  const {rootServerURI} = React.useContext(AppContext);

  const reexecute = useJobReexecution({onCompleted: refetch});
  const {buttonRef, menuRef, isMenuOpen, onInteraction, onMenuClick} = useMenuPopover();

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
    // executionPlan (with its asset keys) is only available once the lazy environment query has
    // loaded; until then the "View asset lineage" link has no keys, but the menu item stays
    // disabled until `infoReady` so it is never clicked in that state.
    run: {...run, executionPlan: pipelineRun?.executionPlan},
    repositoryName: repoMatch?.match.repository.name,
    repositoryLocationName: repoMatch?.match.repositoryLocation.name,
    isJob,
  });

  return (
    <>
      {reexecute.launchpadElement}
      <JoinedButtons>
        <AnchorButton to={`/runs/${run.id}`}>{anchorLabel ?? 'View run'}</AnchorButton>
        <Popover
          isOpen={isMenuOpen}
          onInteraction={onInteraction}
          content={
            <Menu ref={menuRef} onClick={onMenuClick}>
              <AISummaryForRunMenuItem run={run} />
              {canCreateIssue && (
                <MenuItem
                  icon="issue"
                  text="Create or link issue"
                  onClick={() => setVisibleDialog('create-issue')}
                />
              )}
              <MenuItem
                style={{minWidth: 200}}
                text={loading ? 'Loading configuration...' : 'View configuration...'}
                disabled={!runConfigYaml}
                icon="open_in_new"
                onClick={() => setVisibleDialog('config')}
              />
              <MenuItem
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
                      <div className={styles.slashShortcut}>t</div>
                    </Box>
                  </div>
                }
                icon="tag"
                onClick={() => setVisibleDialog('tags')}
              />

              {run.pipelineSnapshotId && !isHiddenAssetGroupJob(run.pipelineName) ? (
                <Link
                  className={styles.linkNoUnderline}
                  to={getPipelineSnapshotLink(run.pipelineName, run.pipelineSnapshotId)}
                >
                  <MenuItem
                    icon="history"
                    text="View snapshot"
                    onClick={() => setVisibleDialog('tags')}
                  />
                </Link>
              ) : null}
              <MenuDivider />
              <>
                <Tooltip
                  content={jobLink.disabledReason || OPEN_LAUNCHPAD_UNKNOWN}
                  position="left"
                  canShow={!infoReady || !!jobLink.disabledReason}
                >
                  <MenuLink
                    text={jobLink.label}
                    disabled={!infoReady || !!jobLink.disabledReason}
                    icon={jobLink.icon}
                    to={jobLink.to}
                  />
                </Tooltip>
                <Tooltip
                  content={reexecutionDisabledState.message || 'Shift-click to adjust tags.'}
                  position="left"
                >
                  <MenuItem
                    text="Re-execute"
                    disabled={reexecutionDisabledState.disabled}
                    icon={reexecute.loading ? <Spinner purpose="caption-text" /> : 'refresh'}
                    onClick={async (e) => {
                      await reexecute.onClick(run, ReexecutionStrategy.ALL_STEPS, e.shiftKey);
                    }}
                  />
                </Tooltip>
                {isFinished || !run.hasTerminatePermission ? null : (
                  <MenuItem
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
                  icon="asset_plot"
                  text="View container metrics"
                  intent="none"
                  onClick={() => setVisibleDialog('metrics')}
                />
              ) : null}
              {run.hasDeletePermission ? (
                <MenuItem
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
          <Button ref={buttonRef} icon={<Icon name="expand_more" />} />
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
          selectedRuns={{[run.id]: run.canTerminate && run.hasTerminatePermission}}
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
          <CopyButton value={() => tagsAsYamlString(run.tags)}>Copy tags</CopyButton>
          <Button intent="primary" onClick={closeDialogs}>
            Close
          </Button>
        </DialogFooter>
      </Dialog>
      <RunConfigDialog
        isOpen={visibleDialog === 'config'}
        onClose={closeDialogs}
        mode={run.mode}
        runConfigYaml={runConfigYaml || ''}
        isJob={isJob}
      />
      {canCreateIssue && (
        <CreateIssueForRunDialog
          isOpen={visibleDialog === 'create-issue'}
          onClose={closeDialogs}
          runId={run.id}
        />
      )}
    </>
  );
});

type BulkRunActionMenuItemProps = {
  icon: IconName;
  intent?: 'danger';
  formatLabel: (runCount: string) => string;
  /** Selected runs whose status the action applies to. */
  applicableRuns: RunActionsMenuRunFragment[];
  /** Applicable runs the user has permission for; the item is disabled when empty. */
  permittedRuns: RunActionsMenuRunFragment[];
  onClick: () => void;
};

const BulkRunActionMenuItem = ({
  icon,
  intent,
  formatLabel,
  applicableRuns,
  permittedRuns,
  onClick,
}: BulkRunActionMenuItemProps) => {
  const hasPermission = permittedRuns.length > 0;
  const count = hasPermission ? permittedRuns.length : applicableRuns.length;
  const text = formatLabel(count === 1 ? '1 run' : `${numberFormatter.format(count)} runs`);
  if (hasPermission) {
    return <MenuItem icon={icon} intent={intent} text={text} onClick={onClick} />;
  }

  return (
    <Tooltip content={DEFAULT_DISABLED_REASON} display="block">
      <MenuItem icon={icon} intent={intent} text={text} disabled />
    </Tooltip>
  );
};

interface RunBulkActionsMenuProps {
  selected: RunActionsMenuRunFragment[];
  clearSelection: () => void;
  notice?: React.ReactNode;
}

export const RunBulkActionsMenu = React.memo(
  ({selected, clearSelection, notice}: RunBulkActionsMenuProps) => {
    const {refetch} = React.useContext(RunsQueryRefetchContext);

    const [visibleDialog, setVisibleDialog] = React.useState<
      'none' | 'terminate' | 'terminate-instead' | 'delete' | 'reexecute-from-failure' | 'reexecute'
    >('none');
    const [terminateInsteadMap, setTerminateInsteadMap] = React.useState<Record<string, boolean>>(
      {},
    );

    const unfinishedRuns = selected.filter((r) => !doneStatuses.has(r.status));
    const terminableRuns = unfinishedRuns.filter((r) => r.hasTerminatePermission);
    const terminableMap = Object.fromEntries(terminableRuns.map((r) => [r.id, r.canTerminate]));

    const deletableRuns = selected.filter((r) => r.hasDeletePermission);
    const deletionMap = Object.fromEntries(
      deletableRuns.map((r) => [r.id, r.canTerminate && r.hasTerminatePermission]),
    );

    const failedRuns = selected.filter((r) => failedStatuses.has(r.status));
    const reexecuteFromFailureRuns = failedRuns.filter((r) => r.hasReExecutePermission);
    const reexecuteFromFailureMap = Object.fromEntries(
      reexecuteFromFailureRuns.map((r) => [r.id, r.id]),
    );

    const finishedRuns = selected.filter((r) => doneStatuses.has(r.status));
    const reexecutableRuns = finishedRuns.filter((r) => r.hasReExecutePermission);
    const reexecutableMap = Object.fromEntries(reexecutableRuns.map((r) => [r.id, r.id]));

    const selectedRunBackfillIds = uniq(
      selected
        .map((r) => r.tags.find((t) => t.key === DagsterTag.Backfill)?.value ?? '')
        .filter(Boolean),
    );

    const isSelectionEmpty = selected.length === 0;

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
          disabled={isSelectionEmpty}
          content={
            <Menu>
              {notice}
              {unfinishedRuns.length > 0 && (
                <BulkRunActionMenuItem
                  icon="cancel"
                  formatLabel={(runCount) => `Terminate ${runCount}`}
                  applicableRuns={unfinishedRuns}
                  permittedRuns={terminableRuns}
                  onClick={() => setVisibleDialog('terminate')}
                />
              )}
              <BulkRunActionMenuItem
                icon="delete"
                intent="danger"
                formatLabel={(runCount) => `Delete ${runCount}`}
                applicableRuns={selected}
                permittedRuns={deletableRuns}
                onClick={() => setVisibleDialog('delete')}
              />
              {finishedRuns.length > 0 && (
                <BulkRunActionMenuItem
                  icon="refresh"
                  formatLabel={(runCount) => `Re-execute ${runCount}`}
                  applicableRuns={finishedRuns}
                  permittedRuns={reexecutableRuns}
                  onClick={() => setVisibleDialog('reexecute')}
                />
              )}
              {failedRuns.length > 0 && (
                <BulkRunActionMenuItem
                  icon="refresh"
                  formatLabel={(runCount) => `Re-execute ${runCount} from failure`}
                  applicableRuns={failedRuns}
                  permittedRuns={reexecuteFromFailureRuns}
                  onClick={() => setVisibleDialog('reexecute-from-failure')}
                />
              )}
            </Menu>
          }
          position="bottom-right"
        >
          <Button
            disabled={isSelectionEmpty}
            rightIcon={<Icon name="expand_more" />}
            intent="primary"
          >
            Actions
          </Button>
        </Popover>
        <TerminationDialog
          isOpen={visibleDialog === 'terminate' || visibleDialog === 'terminate-instead'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={visibleDialog === 'terminate-instead' ? terminateInsteadMap : terminableMap}
        />
        <DeletionDialog
          isOpen={visibleDialog === 'delete'}
          onClose={closeDialogs}
          onComplete={onComplete}
          onTerminateInstead={(runIds) => {
            setTerminateInsteadMap(Object.fromEntries(runIds.map((id) => [id, true])));
            setVisibleDialog('terminate-instead');
          }}
          selectedRuns={deletionMap}
        />
        <ReexecutionDialog
          isOpen={visibleDialog === 'reexecute-from-failure'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={reexecuteFromFailureMap}
          selectedRunBackfillIds={selectedRunBackfillIds}
          reexecutionStrategy={ReexecutionStrategy.FROM_FAILURE}
        />
        <ReexecutionDialog
          isOpen={visibleDialog === 'reexecute'}
          onClose={closeDialogs}
          onComplete={onComplete}
          selectedRuns={reexecutableMap}
          selectedRunBackfillIds={selectedRunBackfillIds}
          reexecutionStrategy={ReexecutionStrategy.ALL_STEPS}
        />
      </>
    );
  },
);

// Avoid fetching envYaml, parentPipelineSnapshotId, and executionPlan on load in Runs page,
// since they can be slow.
export const PIPELINE_ENVIRONMENT_QUERY = gql`
  query PipelineEnvironmentQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        pipelineName
        pipelineSnapshotId
        runConfigYaml
        parentPipelineSnapshotId
        repositoryOrigin {
          id
          repositoryName
          repositoryLocationName
        }
        hasRunMetricsEnabled
        executionPlan {
          assetKeys {
            path
          }
        }
      }
    }
  }
`;
