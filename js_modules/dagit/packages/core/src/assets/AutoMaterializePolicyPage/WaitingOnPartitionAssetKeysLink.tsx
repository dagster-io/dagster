import {
  ButtonLink,
  Box,
  Colors,
  TextInput,
  Dialog,
  DialogFooter,
  Button,
  NonIdealState,
  Icon,
} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';

interface Props {
  assetKeysByPartition: Record<string, AssetKey[]>;
}

export const WaitingOnPartitionAssetKeysLink = ({assetKeysByPartition}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const queryLowercase = queryString.toLocaleLowerCase();

  const partitionNames = Object.keys(assetKeysByPartition);
  const count = partitionNames.length;

  const filteredPartitionNames = React.useMemo(() => {
    if (queryLowercase === '') {
      return partitionNames;
    }
    return partitionNames.filter((partitionName) =>
      partitionName.toLowerCase().includes(queryLowercase),
    );
  }, [partitionNames, queryLowercase]);

  const label = React.useMemo(() => (count === 1 ? `1 partition` : `${count} partitions`), [count]);

  const content = () => {
    if (queryString && !filteredPartitionNames.length) {
      return (
        <Box padding={32}>
          <NonIdealState
            icon="search"
            title="No matching partitions"
            description={
              <>
                No matching partitions for <strong>{queryString}</strong>
              </>
            }
          />
        </Box>
      );
    }

    const visiblePartitions = {} as Record<string, AssetKey[]>;
    filteredPartitionNames.forEach((partitionName) => {
      visiblePartitions[partitionName] = assetKeysByPartition[partitionName]!;
    });

    return <VirtualizedPartitionsWaitingOnAssetList assetKeysByPartition={visiblePartitions} />;
  };

  return (
    <>
      <ButtonLink onClick={() => setIsOpen(true)}>{label}</ButtonLink>
      <Dialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        style={{width: '750px', maxWidth: '80vw', minWidth: '500px'}}
        canOutsideClickClose
        canEscapeKeyClose
      >
        <Box
          padding={{horizontal: 24, vertical: 16}}
          flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
          border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        >
          <div style={{fontSize: '16px'}}>
            {count === 1 ? '1 partition' : `${count} partitions`}
          </div>
          {count > 0 ? (
            <TextInput
              icon="search"
              value={queryString}
              onChange={(e) => setQueryString(e.target.value)}
              placeholder="Filter by partition…"
              style={{width: '252px'}}
            />
          ) : null}
        </Box>
        <div style={{height: '272px', overflow: 'hidden'}}>{content()}</div>
        <DialogFooter topBorder>
          <Button onClick={() => setIsOpen(false)}>Close</Button>
        </DialogFooter>
      </Dialog>
    </>
  );
};

interface VirtualizedPartitionsWaitingOnAssetListProps {
  assetKeysByPartition: Record<string, AssetKey[]>;
}

type Row =
  | {
      type: 'partition-name';
      partitionName: string;
      expanded: boolean;
      assetCount: number;
    }
  | {type: 'asset-key'; assetKey: AssetKey};

const VirtualizedPartitionsWaitingOnAssetList = ({
  assetKeysByPartition,
}: VirtualizedPartitionsWaitingOnAssetListProps) => {
  const [expandedPartitions, setExpandedPartitions] = React.useState<Set<string>>(
    () => new Set([]),
  );
  const container = React.useRef<HTMLDivElement | null>(null);

  const allRows = React.useMemo(() => {
    const rows = [] as Row[];
    Object.entries(assetKeysByPartition).forEach(([partitionName, assetKeys]) => {
      const expanded = expandedPartitions.has(partitionName);
      rows.push({type: 'partition-name', partitionName, expanded, assetCount: assetKeys.length});
      if (expanded) {
        const assetRows: Row[] = assetKeys.map((assetKey) => ({type: 'asset-key', assetKey}));
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
                border={
                  index < allRows.length - 1
                    ? {side: 'bottom', width: 1, color: Colors.KeylineGray}
                    : null
                }
              >
                {row.type === 'partition-name' ? (
                  <ExpandablePartitionName
                    partitionName={row.partitionName}
                    expanded={row.expanded}
                    assetCount={row.assetCount}
                    onToggle={onToggle}
                  />
                ) : (
                  <Box padding={{left: 24}}>
                    <AssetLink path={row.assetKey.path} icon="asset" />
                  </Box>
                )}
              </Box>
            </Row>
          );
        })}
      </Inner>
    </Container>
  );
};

interface ExpandablePartitionNameProps {
  partitionName: string;
  assetCount: number;
  expanded: boolean;
  onToggle: (partitionName: string) => void;
}

const ExpandablePartitionName = ({
  partitionName,
  assetCount,
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
      <div>{assetCount === 1 ? `(Waiting on 1 asset)` : `Waiting on ${assetCount} assets`}</div>
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
