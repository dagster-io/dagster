import {Tag, Tooltip} from '@dagster-io/ui';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {VirtualizedJobHeader, VirtualizedJobRow} from '../workspace/VirtualizedJobRow';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';

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

export const OverviewJobsTable: React.FC<Props> = ({repos}) => {
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
      return row?.type === 'header' ? 32 : 64;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedJobHeader />
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
                  onToggleAll={onToggleAll}
                  expanded={expandedKeys.includes(repoAddressAsHumanString(row.repoAddress))}
                  showLocation={duplicateRepoNames.has(row.repoAddress.name)}
                  rightElement={
                    <Tooltip
                      content={row.jobCount === 1 ? '1 job' : `${row.jobCount} jobs`}
                      placement="top"
                    >
                      <Tag>{row.jobCount}</Tag>
                    </Tooltip>
                  }
                />
              ) : (
                <VirtualizedJobRow
                  key={key}
                  name={row.name}
                  isJob={row.isJob}
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
