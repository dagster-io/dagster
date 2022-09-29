import {gql, useMutation} from '@apollo/client';
import {Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {cancelableStatuses} from '../runs/RunStatuses';
import {TerminationDialog} from '../runs/TerminationDialog';
import {BulkActionStatus} from '../types/globalTypes';

import {BackfillTableFragment} from './types/BackfillTableFragment';
import {CancelBackfill, CancelBackfillVariables} from './types/CancelBackfill';

interface Props {
  backfill?: BackfillTableFragment;
  onClose: () => void;
  onComplete: () => void;
}
export const BackfillTerminationDialog = ({backfill, onClose, onComplete}: Props) => {
  const [cancelBackfill] = useMutation<CancelBackfill, CancelBackfillVariables>(
    CANCEL_BACKFILL_MUTATION,
  );
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  if (!backfill) {
    return null;
  }

  const numUnscheduled = (backfill.numPartitions || 0) - (backfill.numRequested || 0);
  const cancel = async () => {
    setIsSubmitting(true);
    await cancelBackfill({variables: {backfillId: backfill.backfillId}});
    onComplete();
    setIsSubmitting(false);
    onClose();
  };

  const unfinishedPartitions = backfill.partitionStatuses.results.filter(
    (partition) =>
      partition.runStatus && partition.runId && partition.runStatus in cancelableStatuses,
  );
  const unfinishedMap =
    unfinishedPartitions?.reduce(
      (accum, partition) =>
        partition && partition.runId ? {...accum, [partition.runId]: true} : accum,
      {},
    ) || {};

  return (
    <>
      <Dialog
        isOpen={!!backfill && backfill.status !== BulkActionStatus.CANCELED && !!numUnscheduled}
        title="Cancel backfill"
        onClose={onClose}
      >
        <DialogBody>
          There {numUnscheduled === 1 ? 'is 1 partition ' : `are ${numUnscheduled} partitions `}
          yet to be queued or launched.
        </DialogBody>
        <DialogFooter>
          <Button intent="none" onClick={onClose}>
            Close
          </Button>
          {isSubmitting ? (
            <Button intent="danger" disabled>
              Canceling...
            </Button>
          ) : (
            <Button intent="danger" onClick={cancel}>
              Cancel backfill
            </Button>
          )}
        </DialogFooter>
      </Dialog>
      <TerminationDialog
        isOpen={
          !!backfill &&
          (!numUnscheduled || backfill.status !== 'REQUESTED') &&
          !!unfinishedPartitions.length
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
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
