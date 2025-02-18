import {
  Button,
  Icon,
  JoinedButtons,
  Menu,
  MenuDivider,
  MenuItem,
  Popover,
  Tooltip,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {useHistory} from 'react-router-dom';

import {BackfillStepStatusDialog, backfillCanShowStepStatus} from './BackfillStepStatusDialog';
import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {BackfillActionsBackfillFragment} from './types/BackfillFragments.types';
import {useReexecuteBackfill} from './useReexecuteBackfill';
import {useResumeBackfill} from './useResumeBackfill';
import {DEFAULT_DISABLED_REASON} from '../../app/Permissions';
import {BulkActionStatus, ReexecutionStrategy} from '../../graphql/types';
import {getBackfillPath} from '../../runs/RunsFeedUtils';
import {runsPathWithFilters} from '../../runs/RunsFilterInput';
import {testId} from '../../testing/testId';
import {AnchorButton} from '../../ui/AnchorButton';

const BULK_ACTION_TERMINAL_STATUSES = [
  BulkActionStatus.COMPLETED,
  BulkActionStatus.FAILED,
  BulkActionStatus.CANCELED,
  BulkActionStatus.COMPLETED_SUCCESS,
  BulkActionStatus.COMPLETED_FAILED,
];

const BULK_ACTION_TERMINAL_WITH_FAILURES = [
  BulkActionStatus.FAILED,
  BulkActionStatus.CANCELED,
  BulkActionStatus.COMPLETED_FAILED,
];

export const BackfillActionsMenu = ({
  backfill,
  refetch,
  anchorLabel,
}: {
  backfill: BackfillActionsBackfillFragment;
  refetch: () => void;
  anchorLabel?: string;
}) => {
  const history = useHistory();

  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.id}`,
    },
  ]);

  const [showTerminateDialog, setShowTerminateDialog] = useState(false);
  const [showStepStatus, setShowStepStatus] = useState(false);

  const resume = useResumeBackfill(backfill, refetch);
  const reexecute = useReexecuteBackfill(backfill, refetch);

  const cancelDisabledState = useMemo(() => {
    if (!backfill.hasCancelPermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (backfill.status !== BulkActionStatus.REQUESTED) {
      return {disabled: true, message: 'Backfill is not in progress.'};
    }
    return {disabled: false};
  }, [backfill]);

  const resumeDisabledState = useMemo(() => {
    if (!backfill.hasResumePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (backfill.status !== BulkActionStatus.FAILED) {
      return {disabled: true, message: 'All partition runs have been launched.'};
    }
    if (!backfill.partitionSet) {
      return {disabled: true, message: 'Backfill partition set is not available.'};
    }
    return {disabled: false};
  }, [backfill]);

  const reexecutionDisabledState = useMemo(() => {
    if (!backfill.hasResumePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (!BULK_ACTION_TERMINAL_STATUSES.includes(backfill.status)) {
      return {disabled: true, message: 'Backfill is still in progress.'};
    }
    return {disabled: false};
  }, [backfill]);

  const reexecutionFromFailureDisabledState = useMemo(() => {
    if (!backfill.hasResumePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (!BULK_ACTION_TERMINAL_WITH_FAILURES.includes(backfill.status)) {
      return {
        disabled: true,
        message: 'Backfill is still in progress or completed without failed materializations.',
      };
    }
    return {disabled: false};
  }, [backfill]);

  const popover = (
    <Popover
      position="bottom-right"
      content={
        <Menu>
          <MenuItem
            text="View backfill runs"
            icon="settings_backup_restore"
            onClick={() => history.push(runsUrl)}
          />
          <MenuItem
            disabled={!backfillCanShowStepStatus(backfill)}
            text="View step status"
            icon="view_list"
            onClick={() => {
              setShowStepStatus(true);
            }}
          />

          <MenuDivider />
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              reexecutionDisabledState.message || 'Launch a new backfill for the same partitions'
            }
          >
            <MenuItem
              icon="refresh"
              tagName="button"
              text="Re-execute"
              disabled={reexecutionDisabledState.disabled}
              onClick={() => reexecute(ReexecutionStrategy.ALL_STEPS)}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              reexecutionFromFailureDisabledState.message ||
              'Launch a new backfill for partitions that were not materialized successfully'
            }
          >
            <MenuItem
              icon="refresh"
              tagName="button"
              text="Re-execute from failure"
              disabled={reexecutionFromFailureDisabledState.disabled}
              onClick={() => reexecute(ReexecutionStrategy.FROM_FAILURE)}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              resumeDisabledState.message ||
              'Launch runs for remaining partitions in the backfill that do not have a corresponding run. Does not retry failed runs.'
            }
          >
            <MenuItem
              disabled={resumeDisabledState.disabled}
              text="Resume and launch runs"
              icon="refresh"
              onClick={() => resume()}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              cancelDisabledState.message || 'Stop queueing runs and cancel unfinished runs.'
            }
          >
            <MenuItem
              text="Cancel backfill"
              icon="cancel"
              intent="danger"
              disabled={cancelDisabledState.disabled}
              onClick={() => setShowTerminateDialog(true)}
            />
          </Tooltip>
        </Menu>
      }
    >
      <Button
        data-testId={testId('backfill_actions_dropdown_toggle')}
        icon={<Icon name="expand_more" />}
      />
    </Popover>
  );

  return (
    <>
      {anchorLabel ? (
        <JoinedButtons>
          <AnchorButton to={getBackfillPath(backfill.id, backfill.isAssetBackfill)}>
            View
          </AnchorButton>
          {popover}
        </JoinedButtons>
      ) : (
        popover
      )}
      <BackfillStepStatusDialog
        backfill={showStepStatus ? backfill : undefined}
        onClose={() => setShowStepStatus(false)}
      />
      <BackfillTerminationDialog
        backfill={showTerminateDialog ? backfill : undefined}
        onClose={() => setShowTerminateDialog(false)}
        onComplete={() => refetch()}
      />
    </>
  );
};
