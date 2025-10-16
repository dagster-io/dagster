import {Tag, Tooltip} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useMemo, useRef} from 'react';

import {OVERVIEW_COLLAPSED_KEY} from './OverviewExpansionKey';
import {
  VirtualizedResourceHeader,
  VirtualizedResourceRow,
} from '../resources/VirtualizedResourceRow';
import {ResourceEntryFragment} from '../resources/types/WorkspaceResourcesQuery.types';
import {Container, Inner} from '../ui/VirtualizedTable';
import {findDuplicateRepoNames} from '../ui/findDuplicateRepoNames';
import {useRepoExpansionState} from '../ui/useRepoExpansionState';
import {RepoRow} from '../workspace/VirtualizedWorkspaceTable';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';

type Repository = {
  repoAddress: RepoAddress;
  resources: ResourceEntryFragment[];
};

interface Props {
  repos: Repository[];
}

interface Resource extends ResourceEntryFragment {
  type: 'resource';
  repoAddress: RepoAddress;
}

type RowType = {type: 'header'; repoAddress: RepoAddress; resourceCount: number} | Resource;

export const OverviewResourcesTable = ({repos}: Props) => {
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
    repos.forEach(({repoAddress, resources}) => {
      flat.push({type: 'header', repoAddress, resourceCount: resources.length});
      const repoKey = repoAddressAsHumanString(repoAddress);
      if (expandedKeys.includes(repoKey)) {
        resources.forEach((resource) => {
          flat.push({type: 'resource', repoAddress, ...resource});
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
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <VirtualizedResourceHeader />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const row: RowType = flattened[index]!;
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
                    content={
                      row.resourceCount === 1 ? '1 resource' : `${row.resourceCount} resources`
                    }
                    placement="top"
                  >
                    <Tag>{row.resourceCount}</Tag>
                  </Tooltip>
                }
              />
            ) : (
              <VirtualizedResourceRow key={key} height={size} start={start} {...row} />
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};
