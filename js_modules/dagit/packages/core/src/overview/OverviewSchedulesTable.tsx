import {Box, Colors, Tag, Tooltip} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, HeaderCell, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {VirtualizedScheduleRow} from '../workspace/VirtualizedScheduleRow';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type Repository = {
  repoAddress: RepoAddress;
  schedules: string[];
};

interface Props {
  repos: Repository[];
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; scheduleCount: number}
  | {type: 'schedule'; repoAddress: RepoAddress; name: string};

const SCHEDULES_EXPANSION_STATE_STORAGE_KEY = 'schedules-virtualized-expansion-state';

export const OverviewScheduleTable: React.FC<Props> = ({repos}) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const {expandedKeys, onToggle} = useRepoExpansionState(SCHEDULES_EXPANSION_STATE_STORAGE_KEY);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, schedules}) => {
      flat.push({type: 'header', repoAddress, scheduleCount: schedules.length});
      const repoKey = repoAddressAsString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        schedules.forEach((name) => {
          flat.push({type: 'schedule', repoAddress, name});
        });
      }
    });
    return flat;
  }, [repos, expandedKeys]);

  const duplicateRepoNames = findDuplicateRepoNames(repos.map(({repoAddress}) => repoAddress.name));

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'header' ? 32 : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <Box
        border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
        style={{
          display: 'grid',
          gridTemplateColumns: '76px 28% 30% 10% 20% 10%',
          height: '32px',
          fontSize: '12px',
          color: Colors.Gray600,
        }}
      >
        <HeaderCell />
        <HeaderCell>Schedule name</HeaderCell>
        <HeaderCell>Schedule</HeaderCell>
        <HeaderCell>Last tick</HeaderCell>
        <HeaderCell>Last run</HeaderCell>
        <HeaderCell>Actions</HeaderCell>
      </Box>
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: RowType = flattened[index];
              const type = row!.type;
              return type === 'header' ? (
                <RepoRow
                  repoAddress={row.repoAddress}
                  key={key}
                  height={size}
                  start={start}
                  onToggle={onToggle}
                  showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                  rightElement={
                    <Tooltip
                      content={
                        row.scheduleCount === 1 ? '1 schedule' : `${row.scheduleCount} schedules`
                      }
                      placement="top"
                    >
                      <Tag intent="primary">{row.scheduleCount}</Tag>
                    </Tooltip>
                  }
                />
              ) : (
                <VirtualizedScheduleRow
                  key={key}
                  name={row.name}
                  repoAddress={row.repoAddress}
                  height={size}
                  start={start}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};
