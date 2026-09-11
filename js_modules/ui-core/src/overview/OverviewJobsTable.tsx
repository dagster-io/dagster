import {Container, Inner, TABLE_HEADER_HEIGHT} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {JobGroupSectionHeader} from './JobGroupSectionHeader';
import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';
import {
  DEFAULT_JOB_GROUP_NAME,
  JobGroupNode,
  allJobGroupPaths,
  buildJobGroupTree,
} from '../jobs/jobGroups';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {VirtualizedObserveJobRow} from '../workspace/VirtualizedObserveJobRow';
import {DynamicRepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type Job = {
  isJob: boolean;
  name: string;
  groupName?: string | null;
};

type Repository = {
  repoAddress: RepoAddress;
  jobs: Job[];
};

interface Props {
  repos: Repository[];
}

type RowType =
  | {type: 'header'; repoAddress: RepoAddress}
  | {
      type: 'group';
      repoAddress: RepoAddress;
      groupName: string;
      groupKey: string;
      depth: number;
    }
  | {type: 'job'; repoAddress: RepoAddress; isJob: boolean; name: string};

export const groupExpansionKey = (repoKey: string, groupName: string) =>
  `${repoKey}:group:${groupName}`;

export const OverviewJobsTable = ({repos}: Props) => {
  const parentRef = useRef<HTMLDivElement | null>(null);

  // Group sections are only rendered for repos that actually make use of job groups, so that
  // users who have not adopted them see the same flat list as before.
  const groupedRepos = useMemo(
    () =>
      repos.map(({repoAddress, jobs}) => {
        const repoKey = repoAddressAsHumanString(repoAddress);
        const groups = buildJobGroupTree(jobs);
        const showGroups =
          groups.length > 1 ||
          groups.some(({path, children}) => path !== DEFAULT_JOB_GROUP_NAME || children.length);
        return {repoAddress, repoKey, groups, showGroups};
      }),
    [repos],
  );

  const allKeys = useMemo(
    () =>
      groupedRepos.flatMap(({repoKey, groups, showGroups}) => [
        repoKey,
        ...(showGroups
          ? allJobGroupPaths(groups).map((path) => groupExpansionKey(repoKey, path))
          : []),
      ]),
    [groupedRepos],
  );

  const {expandedKeys, onToggle, onToggleAll} = useRepoExpansionState(
    OVERVIEW_COLLAPSED_KEY,
    allKeys,
  );

  const flattened: RowType[] = useMemo(() => {
    const expandedKeySet = new Set(expandedKeys);
    const flat: RowType[] = [];

    groupedRepos.forEach(({repoAddress, repoKey, groups, showGroups}) => {
      flat.push({type: 'header', repoAddress});

      if (!expandedKeySet.has(repoKey)) {
        return;
      }

      const pushGroups = (nodes: JobGroupNode<Job>[]) => {
        nodes.forEach((node) => {
          const groupKey = groupExpansionKey(repoKey, node.path);
          if (showGroups) {
            flat.push({
              type: 'group',
              repoAddress,
              groupName: node.name,
              groupKey,
              depth: node.depth,
            });
            // Collapsing a group hides its jobs and every nested subgroup beneath it.
            if (!expandedKeySet.has(groupKey)) {
              return;
            }
          }
          pushGroups(node.children);
          node.jobs.forEach(({isJob, name}) => {
            flat.push({type: 'job', repoAddress, isJob, name});
          });
        });
      };

      pushGroups(groups);
    });

    return flat;
  }, [groupedRepos, expandedKeys]);

  const duplicateRepoNames = findDuplicateRepoNames(repos.map(({repoAddress}) => repoAddress.name));

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'job' ? 64 : TABLE_HEADER_HEIGHT;
    },
    overscan: 10,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <Inner totalHeight={totalHeight}>
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
              const type = row.type;

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

              if (type === 'group') {
                return (
                  <div key={key} ref={rowVirtualizer.measureElement} data-index={index}>
                    <JobGroupSectionHeader
                      groupName={row.groupName}
                      depth={row.depth}
                      expanded={expandedKeys.includes(row.groupKey)}
                      onClick={() => onToggle(row.groupKey)}
                    />
                  </div>
                );
              }

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
            })}
          </div>
        </Inner>
      </Container>
    </div>
  );
};
