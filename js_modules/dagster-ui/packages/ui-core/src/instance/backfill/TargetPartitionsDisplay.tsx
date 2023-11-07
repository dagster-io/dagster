import {Box, Button, ButtonLink, Dialog, DialogFooter, Tag} from '@dagster-io/ui-components';
import React from 'react';

import {AssetBackfillTargetPartitions} from '../../graphql/types';
import {TruncatedTextWithFullTextOnHover} from '../../nav/getLeftNavItemsForOption';
import {VirtualizedItemListForDialog} from '../../ui/VirtualizedItemListForDialog';
import {numberFormatter} from '../../ui/formatters';

const COLLATOR = new Intl.Collator(navigator.language, {sensitivity: 'base', numeric: true});

export const TargetPartitionsDisplay = ({
  targetPartitionCount,
  targetPartitions,
}: {
  targetPartitionCount?: number;
  targetPartitions?: Pick<AssetBackfillTargetPartitions, 'partitionKeys' | 'ranges'>;
}) => {
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);

  const {partitionKeys, ranges} = targetPartitions || {};

  if (partitionKeys) {
    if (partitionKeys.length <= 3) {
      return (
        <Box flex={{direction: 'row', gap: 8, wrap: 'wrap'}}>
          {partitionKeys.map((p) => (
            <Tag key={p}>{p}</Tag>
          ))}
        </Box>
      );
    }

    return (
      <>
        <ButtonLink onClick={() => setIsDialogOpen(true)}>
          {numberFormatter.format(partitionKeys.length)} partitions
        </ButtonLink>
        <Dialog
          isOpen={isDialogOpen}
          title={`Partition selection (${partitionKeys.length})`}
          onClose={() => setIsDialogOpen(false)}
        >
          <div style={{height: '340px', overflow: 'hidden'}}>
            <VirtualizedItemListForDialog
              items={[...partitionKeys].sort((a, b) => COLLATOR.compare(a, b))}
              renderItem={(assetKey) => (
                <div key={assetKey}>
                  <TruncatedTextWithFullTextOnHover text={assetKey} />
                </div>
              )}
            />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  if (ranges) {
    if (ranges.length === 1) {
      const {start, end} = ranges[0]!;
      return (
        <div>
          {start}...{end}
        </div>
      );
    }

    return (
      <>
        <ButtonLink onClick={() => setIsDialogOpen(true)}>
          {numberFormatter.format(ranges.length)} ranges
        </ButtonLink>
        <Dialog
          isOpen={isDialogOpen}
          title={`Partition selection (${ranges?.length})`}
          onClose={() => setIsDialogOpen(false)}
        >
          <div style={{height: '340px', overflow: 'hidden'}}>
            <VirtualizedItemListForDialog
              items={ranges || []}
              renderItem={({start, end}) => {
                return <div key={`${start}:${end}`}>{`${start}...${end}`}</div>;
              }}
            />
          </div>
          <DialogFooter topBorder>
            <Button onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </Dialog>
      </>
    );
  }

  return (
    <div>{targetPartitionCount === 1 ? '1 partition' : `${targetPartitionCount} partitions`}</div>
  );
};
