import {Menu, MenuItem, Popover} from '@dagster-io/ui-components';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {BulkActionStatus, RunStatus} from '../../graphql/types';
import {runsPathWithFilters} from '../../runs/RunsFilterInput';
import {BackfillTableFragment} from '../types/BackfillTable.types';

export function backfillCanCancelSubmission(backfill: {
  hasCancelPermission: boolean;
  isAssetBackfill: boolean;
  status: BulkActionStatus;
  numCancelable: number;
}) {
  return (
    backfill.hasCancelPermission &&
    ((backfill.isAssetBackfill && backfill.status === BulkActionStatus.REQUESTED) ||
      backfill.numCancelable > 0)
  );
}

export function backfillCanCancelRuns(
  backfill: {hasCancelPermission: boolean},
  counts: {[runStatus: string]: number} | null,
) {
  if (!backfill.hasCancelPermission || !counts) {
    return false;
  }
  const queuedCount = counts[RunStatus.QUEUED] || 0;
  const startedCount = counts[RunStatus.STARTED] || 0;
  return queuedCount > 0 || startedCount > 0;
}

export const BackfillActionsMenu = ({
  backfill,
  canCancelRuns,
  canCancelSubmission,
  onTerminateBackfill,
  onResumeBackfill,
  onShowStepStatus,
  children,
}: {
  children: React.ReactNode;
  backfill: BackfillTableFragment;
  canCancelRuns: boolean;
  canCancelSubmission: boolean;
  onTerminateBackfill: (backfill: BackfillTableFragment) => void;
  onResumeBackfill: (backfill: BackfillTableFragment) => void;
  onShowStepStatus: (backfill: BackfillTableFragment) => void;
}) => {
  const history = useHistory();
  const {hasResumePermission} = backfill;

  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.id}`,
    },
  ]);

  return (
    <Popover
      content={
        <Menu>
          {canCancelSubmission ? (
            <MenuItem
              text="Cancel backfill submission"
              icon="cancel"
              intent="danger"
              onClick={() => onTerminateBackfill(backfill)}
            />
          ) : null}
          {canCancelRuns ? (
            <MenuItem
              text="Terminate unfinished runs"
              icon="cancel"
              intent="danger"
              onClick={() => onTerminateBackfill(backfill)}
            />
          ) : null}
          {hasResumePermission &&
          backfill.status === BulkActionStatus.FAILED &&
          backfill.partitionSet ? (
            <MenuItem
              text="Resume failed backfill"
              title="Submits runs for all partitions in the backfill that do not have a corresponding run. Does not retry failed runs."
              icon="refresh"
              onClick={() => onResumeBackfill(backfill)}
            />
          ) : null}
          <MenuItem
            text="View backfill runs"
            icon="settings_backup_restore"
            onClick={() => history.push(runsUrl)}
          />
          <MenuItem
            text="View step status"
            icon="view_list"
            onClick={() => {
              onShowStepStatus(backfill);
            }}
          />
        </Menu>
      }
      position="bottom-right"
    >
      {children}
    </Popover>
  );
};
