import {Box, Caption, Colors, Icon, MonoSmall, Spinner, Tag} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useEffect, useMemo, useRef} from 'react';
import styled from 'styled-components';

import {AssetEventGroup} from './groupByPartition';
import {Timestamp} from '../app/time/Timestamp';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

// This component is on the feature-flagged AssetOverview page and replaces AssetEventTable

export const AssetEventList = ({
  groups,
  focused,
  setFocused,
  xAxis,
  loading,
  onLoadMore,
}: {
  xAxis: 'time' | 'partition';
  groups: AssetEventGroup[];
  focused?: AssetEventGroup;
  setFocused?: (item: AssetEventGroup | undefined) => void;

  loading: boolean;
  onLoadMore: () => void;
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
  }, [focused?.timestamp, focused?.partition]);

  return (
    <Box
      style={{position: 'relative', flex: 1, minHeight: 0}}
      padding={{vertical: 12, horizontal: 16}}
    >
      <AssetListContainer
        ref={parentRef}
        onScroll={(e) => {
          if (
            !loading &&
            e.currentTarget.scrollHeight > e.currentTarget.clientHeight &&
            e.currentTarget.clientHeight + e.currentTarget.scrollTop >= e.currentTarget.scrollHeight
          ) {
            onLoadMore();
          }
        }}
      >
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
                  padding={{left: 12, right: 8, vertical: 5 as any}}
                  flex={{direction: 'column', justifyContent: 'center', gap: 8}}
                  data-index={index}
                  ref={rowVirtualizer.measureElement}
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

      {loading ? (
        <Box
          style={{position: 'absolute', bottom: 12, left: 0, right: 0}}
          flex={{alignItems: 'center', justifyContent: 'center'}}
        >
          <Box
            style={{borderRadius: 6}}
            padding={{vertical: 8, horizontal: 12}}
            flex={{gap: 4, alignItems: 'center', justifyContent: 'center'}}
            background={Colors.backgroundLighter()}
          >
            <Spinner purpose="body-text" />
            Loading...
          </Box>
        </Box>
      ) : undefined}
    </Box>
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
  border-radius: 8px;

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
  const failed = latest?.__typename === 'FailedToMaterializeEvent';
  return (
    <>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'flex-start'}}>
        <Icon name="partition" />
        {partition}
        <div style={{flex: 1}} />
        {!latest ? (
          <Tag intent="none">Missing</Tag>
        ) : failed ? (
          <Tag intent="danger">Failed</Tag>
        ) : (
          <Tag intent="success">Materialized</Tag>
        )}
      </Box>

      <Caption color={Colors.textLight()} style={{userSelect: 'none'}}>
        {failed ? (
          <span>
            Failed <Timestamp timestamp={{ms: Number(timestamp)}} />
          </span>
        ) : timestamp ? (
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

const AssetEventListEventRow = ({group}: {group: AssetEventGroup}) => {
  const {latest, partition, timestamp} = group;

  const icon = useMemo(() => {
    switch (latest?.__typename) {
      case 'MaterializationEvent':
        return <Icon name="run_success" color={Colors.accentGreen()} size={16} />;
      case 'ObservationEvent':
        return <Icon name="observation" color={Colors.accentGreen()} size={16} />;
      case 'FailedToMaterializeEvent':
        return <Icon name="run_failed" color={Colors.accentRed()} size={16} />;
    }
    return null;
  }, [latest?.__typename]);

  return (
    <Box flex={{direction: 'column', gap: 4}}>
      <Box flex={{gap: 4, direction: 'row', alignItems: 'center'}}>
        {icon}
        <Timestamp timestamp={{ms: Number(timestamp)}} />
      </Box>
      {partition ? (
        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
          <Icon name="partition" />
          <MonoSmall color={Colors.textLight()}>{partition}</MonoSmall>
        </Box>
      ) : undefined}
    </Box>
  );
};
