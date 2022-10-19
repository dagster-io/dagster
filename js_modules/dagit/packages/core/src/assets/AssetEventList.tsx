import {Box, Caption, Colors, Icon, Tag} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Timestamp} from '../app/time/Timestamp';
import {AssetRunLink} from '../asset-graph/AssetNode';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {AssetEventGroup} from './groupByPartition';

// This component is on the feature-flagged AssetOverview page and replaces AssetEventTable

export const AssetEventList: React.FC<{
  xAxis: 'time' | 'partition';
  hasPartitions: boolean;
  hasLineage: boolean;
  groups: AssetEventGroup[];
  focused?: AssetEventGroup;
  setFocused?: (timestamp: AssetEventGroup | undefined) => void;
}> = ({groups, focused, setFocused, xAxis}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: groups.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <Container ref={parentRef}>
      <Inner $totalHeight={totalHeight}>
        {items.map(({index, key, size, start}) => {
          const group = groups[index];
          return (
            <ClickableRow
              key={key}
              $height={size}
              $start={start}
              $focused={group === focused}
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
    background: #faf9f7;
  }
  ${(p) =>
    p.$focused &&
    `background: #faf9f7;
    `}
`;

const AssetEventListPartitionRow: React.FC<{group: AssetEventGroup}> = ({group}) => {
  const {partition, latest, timestamp} = group;
  return (
    <>
      <Box flex={{gap: 4, direction: 'row'}}>
        <Icon name="partition" />
        {partition}
        <div style={{flex: 1}} />
        {!latest ? <Tag intent="none">Missing</Tag> : <Tag intent="success">Materialized</Tag>}
      </Box>

      <Caption color={Colors.Gray600}>
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
        {partition && <Tag icon="partition">{partition}</Tag>}
        {latest && run && (
          <Tag>
            <AssetRunLink
              runId={run.runId}
              event={{stepKey: latest.stepKey, timestamp: latest.timestamp}}
            >
              <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
                <RunStatusWithStats runId={run.runId} status={run.status} size={8} />
                {titleForRun(run)}
              </Box>
            </AssetRunLink>
          </Tag>
        )}
      </Box>
    </>
  );
};
