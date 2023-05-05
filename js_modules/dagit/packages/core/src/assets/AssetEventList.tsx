import {Box, Caption, Colors, Icon, Tag} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {AssetEventGroup} from './groupByPartition';

// This component is on the feature-flagged AssetOverview page and replaces AssetEventTable

export const AssetEventList: React.FC<{
  xAxis: 'time' | 'partition';
  groups: AssetEventGroup[];
  focused?: AssetEventGroup;
  setFocused?: (item: AssetEventGroup | undefined) => void;
}> = ({groups, focused, setFocused, xAxis}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const focusedRowRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: groups.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
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
    <AssetListContainer ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const group = groups[index];
          return (
            <AssetListRow
              key={key}
              $height={size}
              $start={start}
              $focused={group === focused}
              ref={group === focused ? focusedRowRef : undefined}
              onClick={(e) => {
                // If you're interacting with something in the row, don't trigger a focus change.
                // Since focus is stored in the URL bar this overwrites any link click navigation.
                // We could alternatively e.preventDefault() on every link but it's easy to forget.
                if (e.target instanceof HTMLElement && e.target.closest('a')) {
                  return;
                }
                setFocused?.(focused !== group ? group : undefined);
              }}
            >
              <Box
                style={{height: size}}
                padding={{left: 24, right: 12}}
                flex={{direction: 'column', justifyContent: 'center', gap: 8}}
                border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
              >
                {xAxis === 'partition' ? (
                  <AssetEventListPartitionRow group={group} />
                ) : (
                  <AssetEventListEventRow group={group} />
                )}
              </Box>
            </AssetListRow>
          );
        })}
      </Inner>
    </AssetListContainer>
  );
};

export const AssetListContainer = styled(Container)`
  outline: none;
  &:focus {
    box-shadow: 0 -1px ${Colors.Blue500};
  }
`;

export const AssetListRow = styled(Row)<{$focused: boolean}>`
  cursor: pointer;
  user-select: none;

  :focus,
  :active,
  :hover {
    outline: none;
    background: ${Colors.Gray100};
  }
  ${(p) =>
    p.$focused &&
    `background: ${Colors.Blue50};
     color: ${Colors.Blue700};
     :hover {
       background: ${Colors.Blue50};
     }
    `}
`;

const AssetEventListPartitionRow: React.FC<{group: AssetEventGroup}> = ({group}) => {
  const {partition, latest, timestamp} = group;
  return (
    <>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'flex-start'}}>
        <Icon name="partition" />
        {partition}
        <div style={{flex: 1}} />
        {!latest ? <Tag intent="none">Missing</Tag> : <Tag intent="success">Materialized</Tag>}
      </Box>

      <Caption color={Colors.Gray600} style={{userSelect: 'none'}}>
        {timestamp ? (
          <span>
            Materialized <Timestamp timestamp={{ms: Number(timestamp)}} />
          </span>
        ) : (
          'Never materialized'
        )}
      </Caption>
    </>
  );
};

const AssetEventListEventRow: React.FC<{group: AssetEventGroup}> = ({group}) => {
  const {latest, partition, timestamp} = group;
  const run = latest?.runOrError.__typename === 'Run' ? latest.runOrError : null;

  return (
    <>
      <Box flex={{gap: 4, direction: 'row'}}>
        {latest?.__typename === 'MaterializationEvent' ? (
          <Icon name="materialization" />
        ) : (
          <Icon name="observation" />
        )}
        <Timestamp timestamp={{ms: Number(timestamp)}} />
      </Box>
      <Box flex={{gap: 4, direction: 'row'}}>
        {partition && <Tag>{partition}</Tag>}
        {latest && run && (
          <Tag>
            <AssetRunLink
              runId={run.id}
              event={{stepKey: latest.stepKey, timestamp: latest.timestamp}}
            >
              <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
                <RunStatusWithStats runId={run.id} status={run.status} size={8} />
                {titleForRun(run)}
              </Box>
            </AssetRunLink>
          </Tag>
        )}
      </Box>
    </>
  );
};
