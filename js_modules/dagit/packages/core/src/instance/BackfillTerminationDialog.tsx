import {useMutation, useQuery} from '@apollo/client';
import {Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui';
import * as React from 'react';

import {graphql} from '../graphql';
import {cancelableStatuses} from '../runs/RunStatuses';
import {TerminationDialog} from '../runs/TerminationDialog';
import {BulkActionStatus} from '../types/globalTypes';

import {SINGLE_BACKFILL_QUERY} from './BackfillRow';
import {BackfillTableFragment} from './types/BackfillTableFragment';

interface Props {
  backfill?: BackfillTableFragment;
  onClose: () => void;
  onComplete: () => void;
}
export const BackfillTerminationDialog = ({backfill, onClose, onComplete}: Props) => {
  const [cancelBackfill] = useMutation(CANCEL_BACKFILL_MUTATION);
  const {data} = useQuery(SINGLE_BACKFILL_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      backfillId: backfill?.backfillId || '',
    },
    notifyOnNetworkStatusChange: true,
    skip: !backfill,
  });
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const unfinishedMap = React.useMemo(() => {
    if (!backfill || !data || data.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return {};
    }
    const unfinishedPartitions = data.partitionBackfillOrError.partitionStatuses.results.filter(
      (partition) =>
        partition.runStatus && partition.runId && cancelableStatuses.has(partition.runStatus),
    );
    return (
      unfinishedPartitions.reduce(
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
    await cancelBackfill({variables: {backfillId: backfill.backfillId}});
    onComplete();
    setIsSubmitting(false);
    onClose();
  };

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
          !!Object.keys(unfinishedMap).length
        }
        onClose={onClose}
        onComplete={onComplete}
        selectedRuns={unfinishedMap}
      />
    </>
  );
};

const CANCEL_BACKFILL_MUTATION = graphql(`
  mutation CancelBackfill($backfillId: String!) {
    cancelPartitionBackfill(backfillId: $backfillId) {
      __typename
      ... on CancelBackfillSuccess {
        backfillId
      }
      ...PythonErrorFragment
    }
  }
`);
