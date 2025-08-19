import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';
import {useFeatureFlags} from '../app/useFeatureFlags';
import {Container, Inner, TABLE_HEADER_HEIGHT} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {VirtualizedJobHeader, VirtualizedJobRow} from '../workspace/VirtualizedJobRow';
import {VirtualizedObserveJobRow} from '../workspace/VirtualizedObserveJobRow';
import {DynamicRepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type Repository = {
  repoAddress: RepoAddress;
  jobs: {
    isJob: boolean;
    name: string;
  }[];
};

interface Props {
  repos: Repository[];
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress; jobCount: number}
  | {type: 'job'; repoAddress: RepoAddress; isJob: boolean; name: string};

export const OverviewJobsTable = ({repos}: Props) => {
  const {flagUseNewObserveUIs} = useFeatureFlags();
  const parentRef = useRef<HTMLDivElement | null>(null);
  const allKeys = useMemo(
    () => repos.map(({repoAddress}) => repoAddressAsHumanString(repoAddress)),
    [repos],
  );

  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const flattened: RowType[] = useMemo(() => {
    const flat: RowType[] = [];
    repos.forEach(({repoAddress, jobs}) => {
      flat.push({type: 'header', repoAddress, jobCount: jobs.length});
      const repoKey = repoAddressAsHumanString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        jobs.forEach(({isJob, name}) => {
          flat.push({type: 'job', repoAddress, isJob, name});
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
      return row?.type === 'header' ? TABLE_HEADER_HEIGHT : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        {flagUseNewObserveUIs ? null : <VirtualizedJobHeader />}
        <Inner $totalHeight={totalHeight}>
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              transform: `translateY(${items[0]?.start ?? 0}px)`,
            }}
          >
            {items.map(({index, key}) => {
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const row: RowType = flattened[index]!;
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const type = row!.type;

              if (type === 'header') {
                return (
                  <DynamicRepoRow
                    key={key}
                    repoAddress={row.repoAddress}
                    ref={rowVirtualizer.measureElement}
                    index={index}
                    onToggle={onToggle}
                    onToggleAll={onToggleAll}
                    expanded={expandedKeys.includes(repoAddressAsHumanString(row.repoAddress))}
                    showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                    rightElement={<></>}
                  />
                );
              }

              if (flagUseNewObserveUIs) {
                return (
                  <VirtualizedObserveJobRow
                    key={key}
                    index={index}
                    ref={rowVirtualizer.measureElement}
                    name={row.name}
                    isJob={row.isJob}
                    repoAddress={row.repoAddress}
                  />
                );
              }

              return (
                <VirtualizedJobRow
                  key={key}
                  index={index}
                  ref={rowVirtualizer.measureElement}
                  name={row.name}
                  isJob={row.isJob}
                  repoAddress={row.repoAddress}
                />
              );
            })}
          </div>
        </Inner>
      </Container>
    </div>
  );
};
