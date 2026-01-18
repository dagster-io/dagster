import {Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';
import {useState} from 'react';

import {BackfillTerminationDialogBackfillFragment} from './types/BackfillFragments.types';
import {
  CancelBackfillMutation,
  CancelBackfillMutationVariables,
} from './types/BackfillTerminationDialog.types';
import {gql, useMutation} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';

interface Props {
  backfill?: BackfillTerminationDialogBackfillFragment;
  onClose: () => void;
  onComplete: () => void;
}

export const BackfillTerminationDialog = ({backfill, onClose, onComplete}: Props) => {
  const [cancelBackfill] = useMutation<CancelBackfillMutation, CancelBackfillMutationVariables>(
    CANCEL_BACKFILL_MUTATION,
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  if (!backfill) {
    return null;
  }

  const cancel = async () => {
    setIsSubmitting(true);
    await cancelBackfill({variables: {backfillId: backfill.id}});
    onComplete();
    setIsSubmitting(false);
    onClose();
  };

  return (
    <>
      <Dialog isOpen={!!backfill} title="Cancel backfill" onClose={onClose}>
        <DialogBody>
          In progress runs associated with this backfill will be canceled and additional runs will
          not be queued or launched.
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
