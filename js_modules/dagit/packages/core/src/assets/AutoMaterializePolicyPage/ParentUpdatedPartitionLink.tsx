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
  Tag,
  Caption,
} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Container, Inner, Row} from '../../ui/VirtualizedTable';
import {AssetLink} from '../AssetLink';
import {AssetKey} from '../types';

type AssetPartitionDetails = Record<string, {updated: AssetKey[]; willUpdate: AssetKey[]}>;
interface Props {
  updatedAssetKeys: Record<string, AssetKey[]>;
  willUpdateAssetKeys: Record<string, AssetKey[]>;
}

export const ParentUpdatedPartitionLink = ({updatedAssetKeys, willUpdateAssetKeys}: Props) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [queryString, setQueryString] = React.useState('');
  const queryLowercase = queryString.toLocaleLowerCase();

  // combine keys of updatedAssetKeys and willUpdateAssetKeys in to a set with use memo
  const partitionNames = React.useMemo(() => {
    const partitionNames = new Set<string>();
    Object.keys(updatedAssetKeys).forEach((partitionName) => {
      partitionNames.add(partitionName);
    });
    Object.keys(willUpdateAssetKeys).forEach((partitionName) => {
      partitionNames.add(partitionName);
    });
    return Array.from(partitionNames);
  }, [updatedAssetKeys, willUpdateAssetKeys]);

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

    const visiblePartitions = {} as AssetPartitionDetails;
    filteredPartitionNames.forEach((partitionName) => {
      visiblePartitions[partitionName] = {
        updated: updatedAssetKeys[partitionName] || [],
        willUpdate: willUpdateAssetKeys[partitionName] || [],
      };
    });

    return <VirtualizedPartitionsUpdatedAssetList assetPartitionDetails={visiblePartitions} />;
  };

  return (
    <>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <Tag>{label}</Tag>
        <ButtonLink onClick={() => setIsOpen(true)}>
          <Caption>View details</Caption>
        </ButtonLink>
      </Box>
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

interface VirtualizedPartitionsUpdatedAssetListProps {
  assetPartitionDetails: AssetPartitionDetails;
}

type Row =
  | {
      type: 'partition-name';
      partitionName: string;
      expanded: boolean;
      assetCount: number;
    }
  | {type: 'updated-asset-key' | 'will-update-asset-key'; assetKey: AssetKey};

const VirtualizedPartitionsUpdatedAssetList = ({
  assetPartitionDetails,
}: VirtualizedPartitionsUpdatedAssetListProps) => {
  const [expandedPartitions, setExpandedPartitions] = React.useState<Set<string>>(
    () => new Set([]),
  );
  const container = React.useRef<HTMLDivElement | null>(null);

  const allRows = React.useMemo(() => {
    const rows = [] as Row[];
    Object.entries(assetPartitionDetails).forEach(([partitionName, {updated, willUpdate}]) => {
      const expanded = expandedPartitions.has(partitionName);
      rows.push({
        type: 'partition-name',
        partitionName,
        expanded,
        assetCount: updated.length + willUpdate.length,
      });
      if (expanded) {
        const updatedRows: Row[] = updated.map((assetKey) => ({
          type: 'updated-asset-key',
          assetKey,
        }));
        rows.push(...updatedRows);
        const willUpdateRows: Row[] = willUpdate.map((assetKey) => ({
          type: 'will-update-asset-key',
          assetKey,
        }));
        rows.push(...willUpdateRows);
      }
    });
    return rows;
  }, [assetPartitionDetails, expandedPartitions]);

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
                ) : row.type === 'updated-asset-key' ? (
                  <Box padding={{left: 24}}>
                    <AssetLink path={row.assetKey.path} icon="asset" />
                    &nbsp; (Updated)
                  </Box>
                ) : (
                  <Box padding={{left: 24}}>
                    <AssetLink path={row.assetKey.path} icon="asset" />
                    &nbsp; (Will update)
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
      <div>{assetCount === 1 ? `(1 parent updated)` : `(${assetCount} parents updated)`}</div>
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
