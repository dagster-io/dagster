import {Box, Caption, Colors, Icon, Tag} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useEffect, useRef} from 'react';
import styled from 'styled-components';

import {RunlessEventTag} from './RunlessEventTag';
import {AssetEventGroup} from './groupByPartition';
import {isRunlessEvent} from './isRunlessEvent';
import {Timestamp} from '../app/time/Timestamp';
import {AssetRunLink} from '../asset-graph/AssetRunLinking';
import {AssetKeyInput} from '../graphql/types';
import {RunStatusWithStats} from '../runs/RunStatusDots';
import {titleForRun} from '../runs/RunUtils';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

// This component is on the feature-flagged AssetOverview page and replaces AssetEventTable

export const AssetEventList = ({
  groups,
  focused,
  setFocused,
  xAxis,
  assetKey,
}: {
  xAxis: 'time' | 'partition';
  groups: AssetEventGroup[];
  assetKey: AssetKeyInput;
  focused?: AssetEventGroup;
  setFocused?: (item: AssetEventGroup | undefined) => void;
}) => {
  const parentRef = useRef<HTMLDivElement | null>(null);
  const focusedRowRef = useRef<HTMLDivElement | null>(null);

  const rowVirtualizer = useVirtualizer({
    count: groups.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 10,
  });
  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  useEffect(() => {
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
          const group = groups[index]!;
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
                border="bottom"
              >
                {xAxis === 'partition' ? (
                  <AssetEventListPartitionRow group={group} />
                ) : (
                  <AssetEventListEventRow group={group} assetKey={assetKey} />
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
    box-shadow: 0 -1px ${Colors.accentBlue()};
  }
`;

export const AssetListRow = styled(Row)<{$focused: boolean}>`
  cursor: pointer;
  user-select: none;

  :focus,
  :active,
  :hover {
    outline: none;
    background: ${Colors.backgroundLight()};
  }
  ${(p) =>
    p.$focused &&
    `background: ${Colors.backgroundBlue()};
     color: ${Colors.textBlue()};
     :hover {
       background: ${Colors.backgroundBlue()};
     }
    `}
`;

const AssetEventListPartitionRow = ({group}: {group: AssetEventGroup}) => {
  const {partition, latest, timestamp} = group;
  return (
    <>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'flex-start'}}>
        <Icon name="partition" />
        {partition}
        <div style={{flex: 1}} />
        {!latest ? <Tag intent="none">Missing</Tag> : <Tag intent="success">Materialized</Tag>}
      </Box>

      <Caption color={Colors.textLight()} style={{userSelect: 'none'}}>
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

const AssetEventListEventRow = ({
  group,
  assetKey,
}: {
  group: AssetEventGroup;
  assetKey: AssetKeyInput;
}) => {
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
        {latest && run ? (
          <Tag>
            <AssetRunLink
              runId={run.id}
              assetKey={assetKey}
              event={{stepKey: latest.stepKey, timestamp: latest.timestamp}}
            >
              <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
                <RunStatusWithStats runId={run.id} status={run.status} size={8} />
                {titleForRun(run)}
              </Box>
            </AssetRunLink>
          </Tag>
        ) : latest && isRunlessEvent(latest) ? (
          <RunlessEventTag tags={latest.tags} />
        ) : undefined}
      </Box>
    </>
  );
};
