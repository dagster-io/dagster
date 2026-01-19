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
      <Dialog isOpen={!!backfill} title="取消回填" onClose={onClose}>
        <DialogBody>
          与此回填关联的进行中运行将被取消，额外的运行将不会被排队或启动。
        </DialogBody>
        <DialogFooter>
          <Button intent="none" onClick={onClose}>
            关闭
          </Button>
          {isSubmitting ? (
            <Button intent="danger" disabled>
              取消中...
            </Button>
          ) : (
            <Button intent="danger" onClick={cancel}>
              取消回填
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
