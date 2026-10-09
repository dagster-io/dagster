import {
  Button,
  Icon,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  Skeleton,
  Tooltip,
} from '@dagster-io/ui-components';
import {NO_LAUNCH_PERMISSION_MESSAGE} from '@shared/launchpad/LaunchRootExecutionButton';
import {AISummaryForRunMenuItem} from '@shared/runs/AISummaryForRunMenuItem';
import {RunMetricsDialog} from '@shared/runs/RunMetricsDialog';
import {useCanCreateIssueForRun} from '@shared/runs/useCanCreateIssueForRun';
import uniqBy from 'lodash/uniqBy';
import {MouseEvent, ReactNode, RefObject, useContext, useEffect, useRef, useState} from 'react';
import * as yaml from 'yaml';

import {RUN_ACTIONS_MENU_QUERY} from './RunActionsMenuQuery';
import {RunDialog} from './RunDialogs';
import styles from './css/RunActionsCell.module.css';
import {MappedRun} from './mapRunsFeedData';
import {showCopySuccessToast} from './showCopySuccessToast';
import {
  RunActionsMenuDetailsFragment,
  RunActionsMenuQuery,
  RunActionsMenuQueryVariables,
} from './types/RunActionsMenuQuery.types';
import {useQuery} from '../../apollo-client';
import {DEFAULT_DISABLED_REASON} from '../../app/Permissions';
import {useCopyToClipboard} from '../../app/browser';
import {isHiddenAssetGroupJob, tokenForAssetKey} from '../../asset-graph/Utils';
import {globalAssetGraphPathForAssets} from '../../assets/globalAssetGraphPathToString';
import {AssetKeyInput, ReexecutionStrategy, RunStatus} from '../../graphql/types';
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

const getAssetGraphPath = (assetKeys: AssetKeyInput[], checks: {assetKey: AssetKeyInput}[]) => {
  const keys = [...assetKeys, ...checks.map(({assetKey}) => assetKey)];
  return globalAssetGraphPathForAssets(uniqBy(keys, tokenForAssetKey));
};

/**
 * Asset graph link for the run's assets and its checks' parents, or null when there are none.
 * Runs without an explicit selection use their execution plan.
 */
const getAssetSelectionPath = (run: MappedRun, details: RunActionsMenuDetailsFragment) => {
  if (run.assetSelectionCount > 0 || run.assetCheckSelectionCount > 0) {
    return getAssetGraphPath(details.assetSelection ?? [], details.assetCheckSelection ?? []);
  }

  const planAssetKeys = details.executionPlan?.assetKeys ?? [];
  return planAssetKeys.length > 0 ? getAssetGraphPath(planAssetKeys, []) : null;
};

type LaunchpadLink =
  | {href: string; disabledReason: null}
  | {href: null; disabledReason: string | null};

const getLaunchpadLink = (
  run: MappedRun,
  details: RunActionsMenuDetailsFragment | null,
  assetSelectionPath: string | null,
  repoMatch: RepoMatch,
  isJob: boolean,
): LaunchpadLink | null => {
  if (
    !details ||
    // Setup-from-run restores config and op selection, so asset runs get View asset selection.
    assetSelectionPath !== null ||
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

const hasRunConfig = (runConfigYaml: string) => {
  const config = yaml.parse(runConfigYaml);
  return typeof config === 'object' && config !== null && Object.keys(config).length > 0;
};

type JobAvailabilityError = ReturnType<typeof useJobAvailabilityErrorForRun>;

type ReexecuteState = {
  disabled: boolean;
  reason: ReactNode;
};

const getReexecuteState = (
  run: MappedRun,
  isLoading: boolean,
  jobError: JobAvailabilityError,
): ReexecuteState => {
  if (!run.hasReExecutePermission) {
    return {
      disabled: true,
      reason: DEFAULT_DISABLED_REASON,
    };
  }
  if (isLoading) {
    return {
      disabled: true,
      reason: null,
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
  const {data, loading} = useQuery<RunActionsMenuQuery, RunActionsMenuQueryVariables>(
    RUN_ACTIONS_MENU_QUERY,
    {
      variables: {runId: run.id},
      // Fetch on every open, so a failed result is retried; cached details show meanwhile.
      fetchPolicy: 'cache-and-network',
    },
  );
  const details = data?.runOrError.__typename === 'Run' ? data.runOrError : null;
  const isLoading = loading && !details;

  const runForWorkspace = {
    pipelineName: run.jobName,
    repositoryOrigin: run.repositoryOrigin,
    pipelineSnapshotId: run.pipelineSnapshotId,
    parentPipelineSnapshotId: details?.parentPipelineSnapshotId,
  };
  const repoMatch = useRepositoryForRunWithParentSnapshot(runForWorkspace);
  const jobError = useJobAvailabilityErrorForRun(runForWorkspace);

  const isJob = isThisThingAJob(repoMatch?.match ?? null, run.jobName);
  const isHiddenJob = isHiddenAssetGroupJob(run.jobName);
  const assetSelectionPath = details ? getAssetSelectionPath(run, details) : null;
  const launchpadLink = getLaunchpadLink(run, details, assetSelectionPath, repoMatch, isJob);

  const runConfigYaml =
    details && hasRunConfig(details.runConfigYaml) ? details.runConfigYaml : null;

  const snapshotId = isHiddenJob ? null : run.pipelineSnapshotId;

  const isQueued = run.runStatus === RunStatus.QUEUED;

  const showMetrics = run.hasRunMetricsEnabled && RunMetricsDialog !== null;

  const reexecute = getReexecuteState(run, isLoading, jobError);

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
    <>
      <span role="status" className={styles.visuallyHidden}>
        {isLoading ? 'Loading' : null}
      </span>
      <Menu ref={menuRef} onClick={handleMenuClick}>
        <MenuItem
          icon="content_copy"
          text="Copy full run ID"
          onClick={() => {
            copy(run.id);
            showCopySuccessToast('Run ID copied');
          }}
        />
        {run.tags.length > 0 && (
          <MenuItem
            icon="tag"
            text="View all tags"
            onClick={() => onOpenDialog({kind: 'tags', run})}
          />
        )}
        <AISummaryForRunMenuItem run={{id: run.id, status: run.runStatus}} />
        {canCreateIssue && (
          <MenuItem
            icon="issue"
            text="Create or link issue"
            onClick={() => onOpenDialog({kind: 'create-issue', run})}
          />
        )}
        <MenuDivider className={styles.divider} />
        {isLoading && (
          <li role="none" className={styles.skeletonItem}>
            <Skeleton $height={20} />
          </li>
        )}
        {launchpadLink !== null &&
          (launchpadLink.href !== null ? (
            <MenuLink icon="edit" text="Open in Launchpad" to={launchpadLink.href} />
          ) : (
            <ReasonTooltip reason={launchpadLink.disabledReason}>
              <MenuItem icon="edit" text="Open in Launchpad" disabled />
            </ReasonTooltip>
          ))}
        {assetSelectionPath !== null && (
          <MenuLink icon="lineage" text="View asset selection" to={assetSelectionPath} />
        )}
        {runConfigYaml !== null && (
          <MenuItem
            icon="open_in_new"
            text="View configuration"
            onClick={() => onOpenDialog({kind: 'config', run, runConfigYaml, isJob})}
          />
        )}
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
        <MenuDivider className={styles.divider} />
        <ReasonTooltip reason={reexecute.reason}>
          <MenuItem
            icon="refresh"
            text="Re-execute"
            disabled={reexecute.disabled}
            onClick={onReexecute}
          />
        </ReasonTooltip>
        {!doneStatuses.has(run.runStatus) && (
          <ReasonTooltip reason={!run.hasTerminatePermission ? DEFAULT_DISABLED_REASON : null}>
            <MenuItem
              icon="cancel"
              text="Terminate"
              disabled={!run.hasTerminatePermission}
              onClick={() => onOpenDialog({kind: 'terminate', run})}
            />
          </ReasonTooltip>
        )}
        <ReasonTooltip reason={!run.hasDeletePermission ? DEFAULT_DISABLED_REASON : null}>
          <MenuItem
            icon="delete"
            text="Delete"
            intent="danger"
            disabled={!run.hasDeletePermission}
            onClick={() => onOpenDialog({kind: 'delete', run})}
          />
        </ReasonTooltip>
      </Menu>
    </>
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
