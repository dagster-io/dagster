import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {AssetViewType} from '../assets/useAssetView';
import {AssetKeyInput} from '../graphql/types';
import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedAssetCatalogHeader, VirtualizedAssetRow} from './VirtualizedAssetRow';
import {buildRepoAddress} from './buildRepoAddress';

type Row =
  | {type: 'asset'; path: string[]; asset: AssetTableFragment}
  | {type: 'folder'; path: string[]; assets: AssetTableFragment[]};

interface Props {
  headerCheckbox: React.ReactNode;
  prefixPath: string[];
  groups: {[path: string]: AssetTableFragment[]};
  checkedPaths: Set<string>;
  onToggleFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onWipe: (assets: AssetKeyInput[]) => void;
  showRepoColumn: boolean;
  view?: AssetViewType;
}

export const VirtualizedAssetTable: React.FC<Props> = (props) => {
  const {
    headerCheckbox,
    prefixPath,
    groups,
    checkedPaths,
    onToggleFactory,
    onWipe,
    showRepoColumn,
    view = 'flat',
  } = props;
  const parentRef = React.useRef<HTMLDivElement | null>(null);
  const count = Object.keys(groups).length;

  const rowVirtualizer = useVirtualizer({
    count,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  const rows: Row[] = React.useMemo(() => {
    return Object.keys(groups).map((key) => {
      const path = [...prefixPath, ...JSON.parse(key)];
      const assets = groups[key];
      const isFolder = assets.length > 1 || path.join('/') !== assets[0].key.path.join('/');
      return isFolder ? {type: 'folder', path, assets} : {type: 'asset', path, asset: assets[0]};
    });
  }, [prefixPath, groups]);

  return (
    <>
      <VirtualizedAssetCatalogHeader headerCheckbox={headerCheckbox} view={view} />
      <div style={{overflow: 'hidden'}}>
        <Container ref={parentRef}>
          <Inner $totalHeight={totalHeight}>
            {items.map(({index, key, size, start}) => {
              const row: Row = rows[index];
              const path = JSON.stringify(row.path);
              const rowType = () => {
                if (row.type === 'folder') {
                  return 'folder';
                }
                return row.asset.definition ? 'asset' : 'asset_non_sda';
              };

              const repoAddress = () => {
                if (row.type === 'folder' || !row.asset.definition) {
                  return null;
                }
                const repository = row.asset.definition.repository;
                return buildRepoAddress(repository.name, repository.location.name);
              };

              const wipeableAssets = row.type === 'folder' ? row.assets : [row.asset];

              return (
                <VirtualizedAssetRow
                  key={key}
                  view={view}
                  type={rowType()}
                  path={row.path}
                  definition={row.type === 'asset' ? row.asset.definition : null}
                  repoAddress={repoAddress()}
                  showCheckboxColumn
                  showRepoColumn={showRepoColumn}
                  height={size}
                  start={start}
                  checked={checkedPaths.has(path)}
                  onToggleChecked={onToggleFactory(path)}
                  onWipe={() => onWipe(wipeableAssets.map((a) => a.key))}
                />
              );
            })}
          </Inner>
        </Container>
      </div>
    </>
  );
};
