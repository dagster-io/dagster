import {Tag, Tooltip} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {makeScheduleKey} from '../schedules/makeScheduleKey';
import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {
  VirtualizedScheduleHeader,
  VirtualizedScheduleRow,
} from '../workspace/VirtualizedScheduleRow';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';
import {BasicInstigationStateFragment} from './types/BasicInstigationStateFragment.types';

type ScheduleInfo = {name: string; scheduleState: BasicInstigationStateFragment};

type Repository = {
  repoAddress: RepoAddress;
  schedules: ScheduleInfo[];
};

interface Props {
  repos: Repository[];
  headerCheckbox: React.ReactNode;
  checkedKeys: Set<string>;
  onToggleCheckFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; scheduleCount: number}
  | {type: 'schedule'; repoAddress: RepoAddress; schedule: ScheduleInfo};

export const OverviewScheduleTable = ({
  repos,
  headerCheckbox,
  checkedKeys,
  onToggleCheckFactory,
}: Props) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const allKeys = React.useMemo(
    () => repos.map(({repoAddress}) => repoAddressAsHumanString(repoAddress)),
    [repos],
  );

  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, schedules}) => {
      flat.push({type: 'header', repoAddress, scheduleCount: schedules.length});
      const repoKey = repoAddressAsHumanString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        schedules.forEach((schedule) => {
          flat.push({type: 'schedule', repoAddress, schedule});
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
      <VirtualizedScheduleHeader checkbox={headerCheckbox} />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: RowType = flattened[index];
              const type = row!.type;
              if (type === 'header') {
                return (
                  <RepoRow
                    repoAddress={row.repoAddress}
                    key={key}
                    height={size}
                    start={start}
                    onToggle={onToggle}
                    onToggleAll={onToggleAll}
                    expanded={expandedKeys.includes(repoAddressAsHumanString(row.repoAddress))}
                    showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                    rightElement={
                      <Tooltip
                        content={
                          row.scheduleCount === 1 ? '1 schedule' : `${row.scheduleCount} schedules`
                        }
                        placement="top"
                      >
                        <Tag>{row.scheduleCount}</Tag>
                      </Tooltip>
                    }
                  />
                );
              }

              const scheduleKey = makeScheduleKey(row.repoAddress, row.schedule.name);

              return (
                <VirtualizedScheduleRow
                  key={key}
                  name={row.schedule.name}
                  scheduleState={row.schedule.scheduleState}
                  showCheckboxColumn={!!headerCheckbox}
                  checked={checkedKeys.has(scheduleKey)}
                  onToggleChecked={onToggleCheckFactory(scheduleKey)}
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
