import {
  Box,
  Button,
  Dialog,
  DialogFooter,
  FontFamily,
  SpinnerWithText,
} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {gql, useQuery} from '../../apollo-client';
import {
  BackfillPartitionsDialogContentQuery,
  BackfillPartitionsDialogContentQueryVariables,
} from './types/BackfillPartitionsRequestedDialog.types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

interface Props {
  backfillId?: string;
  onClose: () => void;
}

export const BackfillPartitionsRequestedDialog = ({backfillId, onClose}: Props) => {
  return (
    <Dialog
      isOpen={!!backfillId}
      title={
        <span>
          Partitions requested for backfill:{' '}
          <span style={{fontFamily: FontFamily.monospace}}>{backfillId}</span>
        </span>
      }
      onClose={onClose}
    >
      <DialogContent backfillId={backfillId} />
      <DialogFooter topBorder>
        <Button onClick={onClose}>Done</Button>
      </DialogFooter>
    </Dialog>
  );
};

// Separate component so that we can delay sorting until render.
const DialogContent = (props: {backfillId: string | undefined}) => {
  const queryResult = useQuery<
    BackfillPartitionsDialogContentQuery,
    BackfillPartitionsDialogContentQueryVariables
  >(BACKFILL_PARTTIONS_DIALOG_CONTENT_QUERY, {
    skip: !props.backfillId,
    variables: {
      backfillId: props.backfillId ?? '',
    },
  });

  const {data, loading} = queryResult;

  const sorted = useMemo(() => {
    const names =
      data?.partitionBackfillOrError.__typename === 'PartitionBackfill'
        ? data.partitionBackfillOrError.partitionNames
        : null;

    return [...(names || [])].sort((a, b) => COLLATOR.compare(a, b));
  }, [data]);

  return (
    <div style={{height: '340px', overflow: 'hidden'}}>
      {loading ? (
        <Box style={{padding: 64}} flex={{alignItems: 'center', justifyContent: 'center'}}>
          <SpinnerWithText label="Loading requested partitions…" />
        </Box>
      ) : (
        <VirtualizedItemListForDialog
          items={sorted}
          renderItem={(partitionName) => (
            <div key={partitionName}>
              <TruncatedTextWithFullTextOnHover text={partitionName} />
            </div>
          )}
        />
      )}
    </div>
  );
};

const BACKFILL_PARTTIONS_DIALOG_CONTENT_QUERY = gql`
  query BackfillPartitionsDialogContentQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        partitionNames
      }
    }
  }
`;
