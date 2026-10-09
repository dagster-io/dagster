import {
  Button,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  Tooltip,
} from '@dagster-io/ui-components';
import {NO_LAUNCH_PERMISSION_MESSAGE} from '@shared/launchpad/LaunchRootExecutionButton';
import {AISummaryForRunMenuItem} from '@shared/runs/AISummaryForRunMenuItem';
import {RunMetricsDialog} from '@shared/runs/RunMetricsDialog';
import {useCanCreateIssueForRun} from '@shared/runs/useCanCreateIssueForRun';
import {MouseEvent, ReactNode, RefObject, useContext, useEffect, useRef, useState} from 'react';

import {RunDialog} from './RunDialogs';
import {MappedRun} from './mapRunsFeedData';
import {showCopySuccessToast} from './showCopySuccessToast';
import {DEFAULT_DISABLED_REASON} from '../../app/Permissions';
import {useCopyToClipboard} from '../../app/browser';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {ReexecutionStrategy, RunStatus} from '../../graphql/types';
import {getPipelineSnapshotLink} from '../../pipelines/PipelinePathUtils';
import {MenuLink} from '../../ui/MenuLink';
import {isThisThingAJob} from '../../workspace/WorkspaceContext/util';
import {useRepositoryForRunWithParentSnapshot} from '../../workspace/useRepositoryForRun';
import {OPEN_LAUNCHPAD_UNKNOWN, workspacePipelinePath} from '../../workspace/workspacePath';
import {doneStatuses} from '../RunStatuses';
import {RunsQueryRefetchContext} from '../RunUtils';
import {isExternalRun} from '../externalRuns';
import {useJobAvailabilityErrorForRun} from '../useJobAvailabilityErrorForRun';
import {useJobReexecution} from '../useJobReExecution';

type RepoMatch = ReturnType<typeof useRepositoryForRunWithParentSnapshot>;

type LaunchpadLink =
  | {href: string; disabledReason: null}
  | {href: null; disabledReason: string | null};

const getLaunchpadLink = (
  run: MappedRun,
  repoMatch: RepoMatch,
  isJob: boolean,
): LaunchpadLink | null => {
  // Setup-from-run restores config and op selection, not an asset selection.
  if (
    run.assetSelectionCount > 0 ||
    run.assetCheckSelectionCount > 0 ||
    isHiddenAssetGroupJob(run.jobName) ||
    isExternalRun(run)
  ) {
    return null;
  }

  if (!run.hasReExecutePermission) {
    return {
      href: null,
      disabledReason: NO_LAUNCH_PERMISSION_MESSAGE,
    };
  }

  if (!repoMatch) {
    return {
      href: null,
      disabledReason: OPEN_LAUNCHPAD_UNKNOWN,
    };
  }

  return {
    href: workspacePipelinePath({
      repoName: repoMatch.match.repository.name,
      repoLocation: repoMatch.match.repositoryLocation.name,
      pipelineName: run.jobName,
      isJob,
      path: `/playground/setup-from-run/${run.id}`,
    }),
    disabledReason: null,
  };
};

type JobAvailabilityError = ReturnType<typeof useJobAvailabilityErrorForRun>;

type ReexecuteState = {
  disabled: boolean;
  reason: ReactNode;
};

const getReexecuteState = (run: MappedRun, jobError: JobAvailabilityError): ReexecuteState => {
  if (!run.hasReExecutePermission) {
    return {
      disabled: true,
      reason: DEFAULT_DISABLED_REASON,
    };
  }
  if (jobError) {
    return {
      disabled: jobError.disabled,
      reason: jobError.tooltip ?? null,
    };
  }
  return {
    disabled: false,
    reason: null,
  };
};

type ReasonTooltipProps = {
  reason: ReactNode;
  children: ReactNode;
};

const ReasonTooltip = ({reason, children}: ReasonTooltipProps) => (
  <Tooltip content={reason} position="left" canShow={reason !== null} display="block">
    {children}
  </Tooltip>
);

type RunActionsMenuItemsProps = {
  run: MappedRun;
  canCreateIssue: boolean;
  menuRef: RefObject<HTMLUListElement>;
  onOpenDialog: (dialog: RunDialog) => void;
  onReexecute: () => void;
  onSelect: () => void;
};

const RunActionsMenuItems = ({
  run,
  canCreateIssue,
  menuRef,
  onOpenDialog,
  onReexecute,
  onSelect,
}: RunActionsMenuItemsProps) => {
  const copy = useCopyToClipboard();
  const runForWorkspace = {
    pipelineName: run.jobName,
    repositoryOrigin: run.repositoryOrigin,
    pipelineSnapshotId: run.pipelineSnapshotId,
  };
  const repoMatch = useRepositoryForRunWithParentSnapshot(runForWorkspace);
  const jobError = useJobAvailabilityErrorForRun(runForWorkspace);

  const isJob = isThisThingAJob(repoMatch?.match ?? null, run.jobName);
  const isHiddenJob = isHiddenAssetGroupJob(run.jobName);
  const launchpadLink = getLaunchpadLink(run, repoMatch, isJob);

  const snapshotId = isHiddenJob ? null : run.pipelineSnapshotId;

  const isQueued = run.runStatus === RunStatus.QUEUED;

  const showMetrics = run.hasRunMetricsEnabled && RunMetricsDialog !== null;

  const hasInspectItems = launchpadLink !== null || snapshotId !== null || isQueued || showMetrics;

  const reexecute = getReexecuteState(run, jobError);

  // The popover leaves focus on the button, so move it to the first item, as menu buttons do.
  useEffect(() => {
    menuRef.current
      ?.querySelector<HTMLElement>('[role="menuitem"]:not([aria-disabled="true"])')
      ?.focus();
  }, [menuRef]);

  const handleMenuClick = (event: MouseEvent<HTMLUListElement>) => {
    // Disabled items stop their clicks, so only enabled ones reach here.
    if (event.target instanceof Element && event.target.closest('[role="menuitem"]')) {
      onSelect();
    }
  };

  return (
    <Menu ref={menuRef} onClick={handleMenuClick}>
      <MenuItem
        icon="content_copy"
        text="Copy full run ID"
        onClick={() => {
          copy(run.id);
          showCopySuccessToast('Run ID copied');
        }}
      />
      <AISummaryForRunMenuItem run={{id: run.id, status: run.runStatus}} />
      {canCreateIssue && (
        <MenuItem
          icon="issue"
          text="Create or link issue"
          onClick={() => onOpenDialog({kind: 'create-issue', run})}
        />
      )}
      <MenuDivider />
      {launchpadLink !== null &&
        (launchpadLink.href !== null ? (
          <MenuLink icon="edit" text="Open in Launchpad" to={launchpadLink.href} />
        ) : (
          <ReasonTooltip reason={launchpadLink.disabledReason}>
            <MenuItem icon="edit" text="Open in Launchpad" disabled />
          </ReasonTooltip>
        ))}
      {snapshotId !== null && (
        <MenuLink
          icon="history"
          text="View snapshot"
          to={getPipelineSnapshotLink(run.jobName, snapshotId)}
        />
      )}
      {isQueued && (
        <MenuItem
          icon="history_toggle_off"
          text="View queue criteria"
          onClick={() => onOpenDialog({kind: 'queue-criteria', run})}
        />
      )}
      {showMetrics && (
        <MenuItem
          icon="asset_plot"
          text="View container metrics"
          onClick={() => onOpenDialog({kind: 'metrics', run})}
        />
      )}
      {hasInspectItems && <MenuDivider />}
      <ReasonTooltip reason={reexecute.reason}>
        <MenuItem
          icon="refresh"
          text="Re-execute"
          disabled={reexecute.disabled}
          onClick={onReexecute}
        />
      </ReasonTooltip>
      {!doneStatuses.has(run.runStatus) && (
        <ReasonTooltip reason={run.hasTerminatePermission ? null : DEFAULT_DISABLED_REASON}>
          <MenuItem
            icon="cancel"
            text="Terminate"
            disabled={!run.hasTerminatePermission}
            onClick={() => onOpenDialog({kind: 'terminate', run})}
          />
        </ReasonTooltip>
      )}
      <ReasonTooltip reason={run.hasDeletePermission ? null : DEFAULT_DISABLED_REASON}>
        <MenuItem
          icon="delete"
          text="Delete"
          intent="danger"
          disabled={!run.hasDeletePermission}
          onClick={() => onOpenDialog({kind: 'delete', run})}
        />
      </ReasonTooltip>
    </Menu>
  );
};

type RunActionsCellProps = {
  run: MappedRun;
  onOpenRunDialog: (dialog: RunDialog, triggerElement: HTMLElement) => void;
};

export const RunActionsCell = ({run, onOpenRunDialog}: RunActionsCellProps) => {
  const {refetch} = useContext(RunsQueryRefetchContext);
  const reexecute = useJobReexecution({onCompleted: refetch});
  const canCreateIssue = useCanCreateIssueForRun(run.runStatus);

  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // The popover doesn't manage focus, and the focused item unmounts with the menu.
  const closeMenu = () => {
    if (menuRef.current?.contains(document.activeElement)) {
      buttonRef.current?.focus();
    }
    setIsMenuOpen(false);
  };

  const handleInteraction = (nextOpen: boolean) => {
    if (nextOpen) {
      setIsMenuOpen(true);
    } else {
      closeMenu();
    }
  };

  const openDialog = (dialog: RunDialog) => {
    if (buttonRef.current) {
      onOpenRunDialog(dialog, buttonRef.current);
    }
  };

  const reexecuteRun = () =>
    reexecute.onClick(
      {id: run.id, pipelineName: run.jobName, tags: run.tags},
      ReexecutionStrategy.ALL_STEPS,
      false,
      {behavior: 'toast'},
    );

  return (
    <Popover
      isOpen={isMenuOpen}
      onInteraction={handleInteraction}
      position="bottom-right"
      content={
        <RunActionsMenuItems
          run={run}
          canCreateIssue={canCreateIssue}
          menuRef={menuRef}
          onOpenDialog={openDialog}
          onReexecute={reexecuteRun}
          onSelect={closeMenu}
        />
      }
    >
      <Button
        ref={buttonRef}
        intent="none"
        icon={<Icon name="more_vert" />}
        aria-label="Run actions"
      />
    </Popover>
  );
};
