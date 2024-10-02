import {
  Button,
  Group,
  Icon,
  JoinedButtons,
  Menu,
  MenuItem,
  Popover,
} from '@dagster-io/ui-components';
import {useState} from 'react';
import {useHistory} from 'react-router-dom';

import {BackfillStepStatusDialog, backfillCanShowStepStatus} from './BackfillStepStatusDialog';
import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {RESUME_BACKFILL_MUTATION} from './BackfillUtils';
import {BackfillActionsBackfillFragment} from './types/BackfillFragments.types';
import {ResumeBackfillMutation, ResumeBackfillMutationVariables} from './types/BackfillUtils.types';
import {useMutation} from '../../apollo-client';
import {showCustomAlert} from '../../app/CustomAlertProvider';
import {showSharedToaster} from '../../app/DomUtils';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {BulkActionStatus} from '../../graphql/types';
import {getBackfillPath} from '../../runs/RunsFeedUtils';
import {runsPathWithFilters} from '../../runs/RunsFilterInput';
import {AnchorButton} from '../../ui/AnchorButton';

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

export function backfillCanResume(backfill: {
  hasResumePermission: boolean;
  status: BulkActionStatus;
  partitionSet: {__typename: 'PartitionSet'} | null;
}) {
  return !!(
    backfill.hasResumePermission &&
    backfill.status === BulkActionStatus.FAILED &&
    backfill.partitionSet
  );
}

export function backfillCanCancelRuns(
  backfill: {hasCancelPermission: boolean},
  hasCancelableRuns: boolean,
) {
  if (!backfill.hasCancelPermission || !hasCancelableRuns) {
    return false;
  }
  return hasCancelableRuns;
}

export const BackfillActionsMenu = ({
  backfill,
  canCancelRuns,
  refetch,
  anchorLabel,
}: {
  backfill: BackfillActionsBackfillFragment;
  canCancelRuns: boolean;
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
  const [resumeBackfill] = useMutation<ResumeBackfillMutation, ResumeBackfillMutationVariables>(
    RESUME_BACKFILL_MUTATION,
  );

  const resume = async () => {
    const {data} = await resumeBackfill({variables: {backfillId: backfill.id}});
    if (data && data.resumePartitionBackfill.__typename === 'ResumeBackfillSuccess') {
      refetch();
    } else if (data && data.resumePartitionBackfill.__typename === 'UnauthorizedError') {
      await showSharedToaster({
        message: (
          <Group direction="column" spacing={4}>
            <div>
              Attempted to retry the backfill in read-only mode. This backfill was not retried.
            </div>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else if (data && data.resumePartitionBackfill.__typename === 'PythonError') {
      const error = data.resumePartitionBackfill;
      await showSharedToaster({
        message: <div>An unexpected error occurred. This backfill was not retried.</div>,
        icon: 'error',
        intent: 'danger',
        action: {
          text: 'View error',
          onClick: () =>
            showCustomAlert({
              body: <PythonErrorInfo error={error} />,
            }),
        },
      });
    }
  };

  const canCancelSubmission = backfillCanCancelSubmission(backfill);

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
          <MenuItem
            disabled={!backfillCanResume(backfill)}
            text="Resume failed backfill"
            title="Submits runs for all partitions in the backfill that do not have a corresponding run. Does not retry failed runs."
            icon="refresh"
            onClick={() => resume()}
          />
          <MenuItem
            text={canCancelSubmission ? 'Cancel backfill submission' : 'Terminate unfinished runs'}
            icon="cancel"
            intent="danger"
            disabled={!(canCancelSubmission || canCancelRuns)}
            onClick={() => setShowTerminateDialog(true)}
          />
        </Menu>
      }
    >
      <Button icon={<Icon name="expand_more" />} />
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
