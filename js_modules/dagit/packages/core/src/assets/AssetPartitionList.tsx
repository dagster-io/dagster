import {Box, Colors, Icon, Tag} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PartitionState} from '../partitions/PartitionStatus';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

// This component is on the feature-flagged AssetOverview page and replaces AssetEventTable

export const AssetPartitionList: React.FC<{
  partitionStatusData: {[name: string]: PartitionState};
  partitionKeys: string[];
  focused?: string;
  setFocused?: (assetKey: string | undefined) => void;
}> = ({partitionKeys, focused, setFocused, partitionStatusData}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const focusedRowRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: partitionKeys.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 36,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  React.useEffect(() => {
    if (focusedRowRef.current) {
      const el = focusedRowRef.current;
      if (el && el instanceof HTMLElement && 'scrollIntoView' in el) {
        el.scrollIntoView({block: 'nearest'});
      }
    }
  }, [focused]);

  return (
    <Container ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const partitionKey = partitionKeys[index];
          return (
            <ClickableRow
              key={key}
              $height={size}
              $start={start}
              $focused={partitionKey === focused}
              ref={partitionKey === focused ? focusedRowRef : undefined}
              onClick={(e) => {
                // If you're interacting with something in the row, don't trigger a focus change.
                // Since focus is stored in the URL bar this overwrites any link click navigation.
                // We could alternatively e.preventDefault() on every link but it's easy to forget.
                if (e.target instanceof HTMLElement && e.target.closest('a')) {
                  return;
                }
                setFocused?.(focused !== partitionKey ? partitionKey : undefined);
              }}
            >
              <Box
                style={{height: size}}
                padding={{left: 24, right: 12}}
                flex={{direction: 'column', justifyContent: 'center', gap: 8}}
                border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              >
                <AssetPartitionListRow
                  partitionKey={partitionKey}
                  state={partitionStatusData[partitionKey]}
                />
              </Box>
            </ClickableRow>
          );
        })}
      </Inner>
    </Container>
  );
};

const ClickableRow = styled(Row)<{$focused: boolean}>`
  cursor: pointer;

  :focus,
  :active,
  :hover {
    outline: none;
    background: ${Colors.White};
  }
  ${(p) =>
    p.$focused &&
    `background: ${Colors.White};
    `}
`;

const AssetPartitionListRow: React.FC<{partitionKey: string; state: PartitionState}> = ({
  partitionKey,
  state,
}) => {
  return (
    <Box flex={{gap: 4, direction: 'row', alignItems: 'flex-start'}}>
      <Icon name="partition" />
      {partitionKey}
      <div style={{flex: 1}} />
      {state === PartitionState.MISSING ? (
        <Tag intent="none">Missing</Tag>
      ) : (
        <Tag intent="success">Materialized</Tag>
      )}
    </Box>
  );
};
