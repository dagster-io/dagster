import * as React from 'react';

import {Button, Dialog, DialogFooter, FontFamily} from '@dagster-io/ui-components';

import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {BackfillTableFragment} from './types/BackfillTable.types';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});
interface Props {
  backfill?: BackfillTableFragment;
  onClose: () => void;
}
export const BackfillPartitionsRequestedDialog = ({backfill, onClose}: Props) => {
  return (
    <Dialog
      isOpen={!!backfill}
      title={
        <span>
          Partitions requested for backfill:{' '}
          <span style={{fontSize: '18px', fontFamily: FontFamily.monospace}}>{backfill?.id}</span>
        </span>
      }
      onClose={onClose}
    >
      <DialogContent partitionNames={backfill?.partitionNames || []} />
      <DialogFooter topBorder>
        <Button onClick={onClose}>Done</Button>
      </DialogFooter>
    </Dialog>
  );
};

interface DialogContentProps {
  partitionNames: string[];
}

// Separate component so that we can delay sorting until render.
const DialogContent = (props: DialogContentProps) => {
  const {partitionNames} = props;

  const sorted = React.useMemo(() => {
    return [...(partitionNames || [])].sort((a, b) => COLLATOR.compare(a, b));
  }, [partitionNames]);

  return (
    <div style={{height: '340px', overflow: 'hidden'}}>
      <VirtualizedItemListForDialog
        items={sorted}
        renderItem={(partitionName) => (
          <div key={partitionName}>
            <TruncatedTextWithFullTextOnHover text={partitionName} />
          </div>
        )}
      />
    </div>
  );
};
