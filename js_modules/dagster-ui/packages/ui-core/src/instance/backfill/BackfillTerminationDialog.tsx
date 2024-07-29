import {gql, useMutation, useQuery} from '@apollo/client';
import {Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';

import {SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY} from './BackfillRow';
import {SingleBackfillQuery, SingleBackfillQueryVariables} from './types/BackfillRow.types';
import {
  BackfillTerminationDialogBackfillFragment,
  CancelBackfillMutation,
  CancelBackfillMutationVariables,
} from './types/BackfillTerminationDialog.types';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {BulkActionStatus} from '../../graphql/types';
import {TerminationDialog} from '../../runs/TerminationDialog';

interface Props {
  backfill?: BackfillTerminationDialogBackfillFragment;
  onClose: () => void;
  onComplete: () => void;
}

export const BackfillTerminationDialog = ({backfill, onClose, onComplete}: Props) => {
  const [cancelBackfill] = useMutation<CancelBackfillMutation, CancelBackfillMutationVariables>(
    CANCEL_BACKFILL_MUTATION,
  );
  const {data} = useQuery<SingleBackfillQuery, SingleBackfillQueryVariables>(
    SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
    {
      variables: {
        backfillId: backfill?.id || '',
      },
      notifyOnNetworkStatusChange: true,
      skip: !backfill,
    },
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const unfinishedMap = useMemo(() => {
    if (!backfill || !data || data.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return {};
    }
    return (
      data.partitionBackfillOrError.cancelableRuns?.reduce(
        (accum, run) => {
          if (run && run.runId) {
            accum[run.runId] = true;
          }
          return accum;
        },
        {} as Record<string, boolean>,
      ) || {}
    );
  }, [backfill, data]);
  if (!backfill || !data) {
    return null;
  }

  const numUnscheduled = backfill.numCancelable;
  const cancel = async () => {
    setIsSubmitting(true);
    await cancelBackfill({variables: {backfillId: backfill.id}});
    onComplete();
    setIsSubmitting(false);
    onClose();
  };

  return (
    <>
      <Dialog
        isOpen={
          !!backfill &&
          backfill.status !== BulkActionStatus.CANCELED &&
          (backfill.isAssetBackfill || !!numUnscheduled)
        }
        title="Cancel backfill"
        onClose={onClose}
      >
        {backfill.isAssetBackfill ? (
          <DialogBody>
            Confirm cancellation of asset backfill? This will mark unfinished runs as canceled.
          </DialogBody>
        ) : (
          <DialogBody>
            There {numUnscheduled === 1 ? 'is 1 partition ' : `are ${numUnscheduled} partitions `}
            yet to be queued or launched.
          </DialogBody>
        )}
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
      {unfinishedMap && (
        <TerminationDialog
          isOpen={
            !!backfill &&
            (!numUnscheduled || backfill.status !== 'REQUESTED') &&
            !!Object.keys(unfinishedMap).length
          }
          onClose={onClose}
          onComplete={onComplete}
          selectedRuns={unfinishedMap}
        />
      )}
    </>
  );
};

export const BACKFILL_TERMINATION_DIALOG_BACKFILL_FRAGMENT = gql`
  fragment BackfillTerminationDialogBackfillFragment on PartitionBackfill {
    id
    status
    isAssetBackfill
    numCancelable
  }
`;

const CANCEL_BACKFILL_MUTATION = gql`
  mutation CancelBackfill($backfillId: String!) {
    cancelPartitionBackfill(backfillId: $backfillId) {
      ... on CancelBackfillSuccess {
        backfillId
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
