import {gql} from '@apollo/client';
import {
  Box,
  Icon,
  IconWrapper,
  Tag,
  colorBackgroundLight,
  colorLinkDefault,
} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {AppContext} from '../app/AppContext';
import {ASSET_TABLE_DEFINITION_FRAGMENT} from '../assets/AssetTableFragment';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

import {VirtualizedAssetHeader, VirtualizedAssetRow} from './VirtualizedAssetRow';
import {repoAddressAsHumanString} from './repoAddressAsString';
import {RepoAddress} from './types';
import {RepoAssetTableFragment} from './types/VirtualizedRepoAssetTable.types';
import {workspacePathFromAddress} from './workspacePath';

type Asset = RepoAssetTableFragment;

interface Props {
  repoAddress: RepoAddress;
  assets: Asset[];
}

type RowType =
  | {type: 'group'; name: string; assetCount: number}
  | {type: 'asset'; id: string; definition: Asset};

const UNGROUPED_NAME = 'UNGROUPED';
const ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY = 'assets-virtualized-expansion-state';

export const VirtualizedRepoAssetTable = ({repoAddress, assets}: Props) => {
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const repoKey = repoAddressAsHumanString(repoAddress);
  const {expandedKeys, onToggle} = useAssetGroupExpansionState(
    `${repoKey}-${ASSET_GROUPS_EXPANSION_STATE_STORAGE_KEY}`,
  );

  const grouped: Record<string, Asset[]> = React.useMemo(() => {
    const groups: Record<string, Asset[]> = {};
    for (const asset of assets) {
      const groupName = asset.groupName || UNGROUPED_NAME;
      const assetsForGroup = groups[groupName] || [];
      groups[groupName] = [...assetsForGroup, asset];
    }
    return groups;
  }, [assets]);

  const flattened: RowType[] = React.useMemo(() => {
    const flat: RowType[] = [];
    Object.entries(grouped).forEach(([groupName, assetsForGroup]) => {
      flat.push({type: 'group', name: groupName, assetCount: assetsForGroup.length});
      if (expandedKeys.includes(groupName)) {
        assetsForGroup.forEach((asset) => {
          flat.push({type: 'asset', id: asset.id, definition: asset});
        });
      }
    });
    return flat;
  }, [grouped, expandedKeys]);

  const rowVirtualizer = useVirtualizer({
    count: flattened.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (ii: number) => {
      const row = flattened[ii];
      return row?.type === 'group' ? 48 : 64;
    },
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <>
      <VirtualizedAssetHeader nameLabel="Asset name" />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: RowType = flattened[index]!;
              const type = row!.type;
              return type === 'group' ? (
                <GroupNameRow
                  repoAddress={repoAddress}
                  groupName={row.name}
                  assetCount={row.assetCount}
                  expanded={expandedKeys.includes(row.name)}
                  key={key}
                  height={size}
                  start={start}
                  onToggle={onToggle}
                />
              ) : (
                <VirtualizedAssetRow
                  showCheckboxColumn={false}
                  definition={row.definition}
                  path={row.definition.assetKey.path}
                  key={key}
                  type="asset"
                  repoAddress={repoAddress}
                  showRepoColumn={false}
                  height={size}
                  start={start}
                  checked={false}
                  onToggleChecked={() => {}}
                  onWipe={() => {}}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};

const GroupNameRow = ({
  repoAddress,
  groupName,
  assetCount,
  expanded,
  height,
  start,
  onToggle,
}: {
  repoAddress: RepoAddress;
  groupName: string;
  assetCount: number;
  expanded: boolean;
  height: number;
  start: number;
  onToggle: (groupName: string) => void;
}) => {
  return (
    <ClickableRow
      $height={height}
      $start={start}
      onClick={() => onToggle(groupName)}
      $open={expanded}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.code === 'Space' || e.code === 'Enter') {
          e.preventDefault();
          onToggle(groupName);
        }
      }}
    >
      <Box
        background={colorBackgroundLight()}
        flex={{direction: 'row', alignItems: 'center', gap: 8, justifyContent: 'space-between'}}
        padding={{horizontal: 24}}
        border="bottom"
        style={{height: '100%'}}
      >
        <Box flex={{alignItems: 'center', gap: 8}}>
          <Icon name="asset_group" />
          {groupName === UNGROUPED_NAME ? (
            <div>Ungrouped assets</div>
          ) : (
            <>
              <strong>{groupName}</strong>
              {groupName !== UNGROUPED_NAME ? (
                <Box margin={{left: 12}}>
                  <Link to={workspacePathFromAddress(repoAddress, `/asset-groups/${groupName}`)}>
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                      <span>View lineage</span>
                      <Icon name="open_in_new" size={16} color={colorLinkDefault()} />
                    </Box>
                  </Link>
                </Box>
              ) : null}
            </>
          )}
        </Box>
        <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
          <Tag>{assetCount === 1 ? '1 asset' : `${assetCount} assets`}</Tag>
          <Icon name="arrow_drop_down" size={20} />
        </Box>
      </Box>
    </ClickableRow>
  );
};

const ClickableRow = styled(Row)<{$open: boolean}>`
  cursor: pointer;

  :focus,
  :active {
    outline: none;
  }

  ${IconWrapper}[aria-label="arrow_drop_down"] {
    transition: transform 100ms linear;
    ${({$open}) => ($open ? null : `transform: rotate(-90deg);`)}
  }
`;

const validateExpandedKeys = (parsed: unknown) => (Array.isArray(parsed) ? parsed : []);

/**
 * Use localStorage to persist the expanded/collapsed visual state of asset groups.
 */
const useAssetGroupExpansionState = (storageKey: string) => {
  const {basePath} = React.useContext(AppContext);
  const [expandedKeys, setExpandedKeys] = useStateWithStorage<string[]>(
    `${basePath}:dagster.${storageKey}`,
    validateExpandedKeys,
  );

  const onToggle = React.useCallback(
    (groupName: string) => {
      setExpandedKeys((current) => {
        const nextExpandedKeys = new Set(current || []);
        if (nextExpandedKeys.has(groupName)) {
          nextExpandedKeys.delete(groupName);
        } else {
          nextExpandedKeys.add(groupName);
        }
        return Array.from(nextExpandedKeys);
      });
    },
    [setExpandedKeys],
  );

  return React.useMemo(
    () => ({
      expandedKeys,
      onToggle,
    }),
    [expandedKeys, onToggle],
  );
};

export const REPO_ASSET_TABLE_FRAGMENT = gql`
  fragment RepoAssetTableFragment on AssetNode {
    id
    assetKey {
      path
    }
    groupName
    ...AssetTableDefinitionFragment
  }

  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;
