import {Box, Colors, Icon, IconWrapper, Tag} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import {useRef} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {VirtualizedAssetHeader, VirtualizedAssetRow} from './VirtualizedAssetRow';
import {RepoAddress} from './types';
import {RepoAssetTableFragment} from './types/WorkspaceAssetsQuery.types';
import {useFlattenedGroupedAssetList} from './useFlattenedGroupedAssetList';
import {workspacePathFromAddress} from './workspacePath';
import {Container, Inner, Row} from '../ui/VirtualizedTable';

type Asset = RepoAssetTableFragment;

interface Props {
  repoAddress: RepoAddress;
  assets: Asset[];
}

type RowType =
  | {type: 'group'; name: string; assetCount: number}
  | {type: 'asset'; id: string; definition: Asset};

const UNGROUPED_NAME = 'UNGROUPED';

export const VirtualizedRepoAssetTable = ({repoAddress, assets}: Props) => {
  const parentRef = useRef<HTMLDivElement | null>(null);
  const {flattened, expandedKeys, onToggle} = useFlattenedGroupedAssetList({repoAddress, assets});

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
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <VirtualizedAssetHeader nameLabel="Asset name" />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const row: RowType = flattened[index]!;
            const type = row!.type;
            return type === 'group' ? (
              <GroupNameRow
                repoAddress={repoAddress}
                groupName={row.name}
                assetCount={row.assetCount}
                expanded={expandedKeys.has(row.name)}
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
                onRefresh={() => {}}
              />
            );
          })}
        </Inner>
      </Container>
    </div>
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
        background={Colors.backgroundLight()}
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
                      <Icon name="open_in_new" size={16} color={Colors.linkDefault()} />
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
