import {Box, Icon} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components';

import {COMMON_COLLATOR} from '../../app/Util';
import {Container, Inner, Row} from '../../ui/VirtualizedTable';

interface Props<A> {
  assetKeysByPartition: Record<string, A[]>;
  renderPartitionDetail: (item: PartitionRow) => React.ReactNode;
  renderItem: (item: A) => React.ReactNode;
}

type PartitionRow = {
  type: 'partition-name';
  partitionName: string;
  expanded: boolean;
  assetCount: number;
};

type Row<A> = PartitionRow | {type: 'asset-key'; assetKey: A};

export function VirtualizedAssetPartitionListForDialog<A>({
  assetKeysByPartition,
  renderPartitionDetail,
  renderItem,
}: Props<A>) {
  const [expandedPartitions, setExpandedPartitions] = React.useState<Set<string>>(
    () => new Set([]),
  );
  const container = React.useRef<HTMLDivElement | null>(null);

  const allRows = React.useMemo(() => {
    const rows = [] as Row<A>[];
    const partitionNames = Object.keys(assetKeysByPartition).sort((a, b) =>
      COMMON_COLLATOR.compare(a, b),
    );
    partitionNames.forEach((partitionName) => {
      const assetKeys = assetKeysByPartition[partitionName]!;
      const expanded = expandedPartitions.has(partitionName);
      rows.push({type: 'partition-name', partitionName, expanded, assetCount: assetKeys.length});
      if (expanded) {
        const assetRows: Row<A>[] = assetKeys.map((assetKey) => ({type: 'asset-key', assetKey}));
        rows.push(...assetRows);
      }
    });
    return rows;
  }, [assetKeysByPartition, expandedPartitions]);

  const rowVirtualizer = useVirtualizer({
    count: allRows.length,
    getScrollElement: () => container.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  const onToggle = React.useCallback((partitionName: string) => {
    setExpandedPartitions((current) => {
      const copy = new Set(Array.from(current));
      if (current.has(partitionName)) {
        copy.delete(partitionName);
      } else {
        copy.add(partitionName);
      }
      return copy;
    });
  }, []);

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={container} style={{padding: '8px 24px'}}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const row = allRows[index]!;
          return (
            <Row $height={size} $start={start} key={key}>
              <Box
                style={{height: '100%'}}
                flex={{direction: 'row', alignItems: 'center'}}
                border={index < allRows.length - 1 ? 'bottom' : null}
              >
                {row.type === 'partition-name' ? (
                  <ExpandablePartitionName
                    partitionName={row.partitionName}
                    expanded={row.expanded}
                    detail={renderPartitionDetail(row)}
                    onToggle={onToggle}
                  />
                ) : (
                  <Box padding={{left: 24}}>{renderItem(row.assetKey)}</Box>
                )}
              </Box>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
}

interface ExpandablePartitionNameProps {
  partitionName: string;
  expanded: boolean;
  detail: React.ReactNode;
  onToggle: (partitionName: string) => void;
}

const ExpandablePartitionName = ({
  partitionName,
  detail,
  expanded,
  onToggle,
}: ExpandablePartitionNameProps) => {
  return (
    <PartitionNameButton onClick={() => onToggle(partitionName)}>
      <Icon
        name="arrow_drop_down"
        style={{transform: expanded ? 'rotate(0deg)' : 'rotate(-90deg)'}}
      />
      <div>{partitionName}</div>
      <div>{detail}</div>
    </PartitionNameButton>
  );
};

const PartitionNameButton = styled.button`
  background-color: transparent;
  cursor: pointer;
  padding: 0;
  border: 0;
  display: flex;
  height: 100%;
  width: 100%;
  flex-direction: row;
  align-items: center;
  gap: 8px;

  :focus {
    outline: none;
  }
`;
