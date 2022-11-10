import {Button, DialogBody, DialogFooter, Dialog, FontFamily, Box} from '@dagster-io/ui';
import * as React from 'react';

import {BackfillTableFragment} from './types/BackfillTableFragment';

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
          <span style={{fontSize: '18px', fontFamily: FontFamily.monospace}}>
            {backfill?.backfillId}
          </span>
        </span>
      }
      onClose={onClose}
    >
      <DialogBody>
        {backfill ? (
          <Box flex={{direction: 'column', gap: 8}} style={{maxHeight: '80vh', overflowY: 'auto'}}>
            {backfill.partitionNames.map((partitionName: string) => (
              <div key={partitionName}>{partitionName}</div>
            ))}
          </Box>
        ) : null}
      </DialogBody>
      <DialogFooter topBorder>
        <Button onClick={onClose}>Done</Button>
      </DialogFooter>
    </Dialog>
  );
};
