import {Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import {useState} from 'react';

import {SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY} from './BackfillRow';
import {BackfillTerminationDialogBackfillFragment} from './types/BackfillFragments.types';
import {SingleBackfillQuery, SingleBackfillQueryVariables} from './types/BackfillRow.types';
import {
  CancelBackfillMutation,
  CancelBackfillMutationVariables,
} from './types/BackfillTerminationDialog.types';
import {gql, useMutation, useQuery} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {BulkActionStatus} from '../../graphql/types';

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
    </>
  );
};

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
