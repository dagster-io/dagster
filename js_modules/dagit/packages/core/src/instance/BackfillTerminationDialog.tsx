import {gql, useMutation} from '@apollo/client';
import * as React from 'react';

import {doneStatuses} from '../runs/RunStatuses';
import {TerminationDialog} from '../runs/TerminationDialog';
import {BulkActionStatus} from '../types/globalTypes';
import {ButtonWIP} from '../ui/Button';
import {DialogBody, DialogFooter, DialogWIP} from '../ui/Dialog';

import {InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results} from './types/InstanceBackfillsQuery';

type Backfill = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results;

interface Props {
  backfill?: Backfill;
  onClose: () => void;
  onComplete: () => void;
}
export const BackfillTerminationDialog = ({backfill, onClose, onComplete}: Props) => {
  const [cancelBackfill] = useMutation(CANCEL_BACKFILL_MUTATION);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  if (!backfill) {
    return null;
  }
  const numUnscheduled = (backfill.numTotal || 0) - (backfill.numRequested || 0);
  const cancelableRuns = backfill.runs.filter(
    (run) => !doneStatuses.has(run?.status) && run.canTerminate,
  );
  const unfinishedMap = backfill.runs
    .filter((run) => !doneStatuses.has(run?.status))
    .reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {});

  const cancel = async () => {
    setIsSubmitting(true);
    await cancelBackfill({variables: {backfillId: backfill.backfillId}});
    onComplete();
    setIsSubmitting(false);
  };

  return (
    <>
      <DialogWIP
        isOpen={!!backfill && backfill.status !== BulkActionStatus.CANCELED && !!numUnscheduled}
        title="Cancel backfill"
        onClose={onClose}
      >
        <DialogBody>
          There {numUnscheduled === 1 ? 'is 1 partition ' : `are ${numUnscheduled} partitions `}
          yet to be queued or launched.
        </DialogBody>
        <DialogFooter>
          <ButtonWIP intent="none" onClick={onClose}>
            Close
          </ButtonWIP>
          {isSubmitting ? (
            <ButtonWIP intent="danger" disabled>
              Canceling...
            </ButtonWIP>
          ) : (
            <ButtonWIP intent="danger" onClick={cancel}>
              Cancel backfill
            </ButtonWIP>
          )}
        </DialogFooter>
      </DialogWIP>
      <TerminationDialog
        isOpen={
          !!backfill &&
          (!numUnscheduled || backfill.status !== 'REQUESTED') &&
          !!cancelableRuns.length
        }
        onClose={onClose}
        onComplete={onComplete}
        selectedRuns={unfinishedMap}
      />
    </>
  );
};

const CANCEL_BACKFILL_MUTATION = gql`
  mutation CancelBackfill($backfillId: String!) {
    cancelPartitionBackfill(backfillId: $backfillId) {
      __typename
      ... on CancelBackfillSuccess {
        backfillId
      }
      ... on PythonError {
        message
      }
    }
  }
`;
