import {Button, DialogBody, DialogFooter, Dialog} from '@dagster-io/ui';
import * as React from 'react';

import {BackfillTableFragment} from './types/BackfillTableFragment';

interface Props {
  backfill?: BackfillTableFragment;
  onClose: () => void;
}
export const BackfillPartitionsRequestedDialog = ({backfill, onClose}: Props) => {
  if (!backfill) {
    return null;
  }
  if (!backfill.partitionSet) {
    return null;
  }

  return (
    <Dialog
      isOpen={!!backfill}
      title={
        <span>
          Partitions requested for backfill:{' '}
          <span style={{fontFamily: 'monospace'}}>{backfill.backfillId}</span>
        </span>
      }
      onClose={onClose}
    >
      <DialogBody>
        <div style={{maxHeight: '80vh', overflowY: 'auto'}}>
          {backfill.partitionNames.map((partitionName: string) => (
            <div key={partitionName}>{partitionName}</div>
          ))}
        </div>
      </DialogBody>
      <DialogFooter>
        <Button intent="none" onClick={onClose}>
          Close
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
