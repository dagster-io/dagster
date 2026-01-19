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

  const [showTerminateDialog, setShowTerminateDialog] = useState(false);
  const [showStepStatus, setShowStepStatus] = useState(false);

  const resume = useResumeBackfill(backfill, refetch);
  const reexecute = useReexecuteBackfill(backfill, refetch);

  const cancelDisabledState = useMemo(() => {
    if (!backfill.hasCancelPermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (backfill.status !== BulkActionStatus.REQUESTED) {
      return {disabled: true, message: '回填未在进行中。'};
    }
    return {disabled: false};
  }, [backfill]);

  const resumeDisabledState = useMemo(() => {
    if (!backfill.hasResumePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (backfill.status !== BulkActionStatus.FAILED) {
      return {disabled: true, message: '所有分区运行已启动。'};
    }
    if (!backfill.partitionSet) {
      return {disabled: true, message: '回填分区集不可用。'};
    }
    return {disabled: false};
  }, [backfill]);

  const reexecutionDisabledState = useMemo(() => {
    if (!backfill.hasResumePermission) {
      return {disabled: true, message: DEFAULT_DISABLED_REASON};
    }
    if (!BULK_ACTION_TERMINAL_STATUSES.includes(backfill.status)) {
      return {disabled: true, message: '回填仍在进行中。'};
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
        message: '回填仍在进行中或已完成且无失败的物化。',
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
            text="查看回填运行"
            icon="settings_backup_restore"
            onClick={() => history.push(getBackfillPath(backfill.id, 'runs'))}
          />
          <MenuItem
            disabled={!backfillCanShowStepStatus(backfill)}
            text="查看步骤状态"
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
              reexecutionDisabledState.message || '为相同分区启动新的回填'
            }
          >
            <MenuItem
              icon="refresh"
              tagName="button"
              text="重新执行"
              disabled={reexecutionDisabledState.disabled}
              onClick={() => reexecute(ReexecutionStrategy.ALL_STEPS)}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              reexecutionFromFailureDisabledState.message ||
              '为未成功物化的分区启动新的回填'
            }
          >
            <MenuItem
              icon="refresh"
              tagName="button"
              text="从失败处重新执行"
              disabled={reexecutionFromFailureDisabledState.disabled}
              onClick={() => reexecute(ReexecutionStrategy.FROM_FAILURE)}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              resumeDisabledState.message ||
              '为回填中尚无对应运行的剩余分区启动运行。不会重试失败的运行。'
            }
          >
            <MenuItem
              disabled={resumeDisabledState.disabled}
              text="恢复并启动运行"
              icon="refresh"
              onClick={() => resume()}
            />
          </Tooltip>
          <Tooltip
            position="left"
            targetTagName="div"
            content={
              cancelDisabledState.message || '停止排队运行并取消未完成的运行。'
            }
          >
            <MenuItem
              text="取消回填"
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
        data-testid={testId('backfill_actions_dropdown_toggle')}
        icon={<Icon name="expand_more" />}
      />
    </Popover>
  );

  return (
    <>
      {anchorLabel ? (
        <JoinedButtons>
          <AnchorButton to={getBackfillPath(backfill.id)}>查看</AnchorButton>
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
