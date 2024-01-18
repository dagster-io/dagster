import * as React from 'react';
import {gql, useMutation, useQuery} from '@apollo/client';

import {Button, Dialog, DialogBody, DialogFooter} from '@dagster-io/ui-components';

import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';
import {BulkActionStatus} from '../../graphql/types';
import {cancelableStatuses} from '../../runs/RunStatuses';
import {TerminationDialog} from '../../runs/TerminationDialog';
import {SINGLE_BACKFILL_STATUS_DETAILS_QUERY} from './BackfillRow';
import {SingleBackfillQuery, SingleBackfillQueryVariables} from './types/BackfillRow.types';
import {
  BackfillTerminationDialogBackfillFragment,
  CancelBackfillMutation,
  CancelBackfillMutationVariables,
} from './types/BackfillTerminationDialog.types';

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
    SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
    {
      variables: {
        backfillId: backfill?.id || '',
      },
      notifyOnNetworkStatusChange: true,
      skip: !backfill,
    },
  );
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const unfinishedMap = React.useMemo(() => {
    if (!backfill || !data || data.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return {};
    }
    const unfinishedPartitions = data.partitionBackfillOrError.partitionStatuses?.results.filter(
      (partition) =>
        partition.runStatus && partition.runId && cancelableStatuses.has(partition.runStatus),
    );
    return (
      unfinishedPartitions?.reduce(
        (accum, partition) =>
          partition && partition.runId ? {...accum, [partition.runId]: true} : accum,
        {},
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
