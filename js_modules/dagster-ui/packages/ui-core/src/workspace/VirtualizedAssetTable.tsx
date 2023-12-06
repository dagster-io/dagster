import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {AssetViewType} from '../assets/useAssetView';
import {AssetKeyInput} from '../graphql/types';
import {Container, Inner} from '../ui/VirtualizedTable';

import {VirtualizedAssetCatalogHeader, VirtualizedAssetRow} from './VirtualizedAssetRow';
import {buildRepoAddress} from './buildRepoAddress';

type Row =
  | {type: 'asset'; path: string[]; displayKey: string; asset: AssetTableFragment}
  | {type: 'folder'; path: string[]; displayKey: string; assets: AssetTableFragment[]};

interface Props {
  headerCheckbox: React.ReactNode;
  prefixPath: string[];
  groups: {[displayKey: string]: AssetTableFragment[]};
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onWipe: (assets: AssetKeyInput[]) => void;
  showRepoColumn: boolean;
  view?: AssetViewType;
}

export const VirtualizedAssetTable = (props: Props) => {
  const {
    headerCheckbox,
    prefixPath,
    groups,
    checkedDisplayKeys,
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
    return Object.entries(groups).map(([displayKey, assets]) => {
      const path = [...prefixPath, ...JSON.parse(displayKey)];
      const isFolder = assets.length > 1 || path.join('/') !== assets[0]!.key.path.join('/');
      return isFolder
        ? {type: 'folder', path, displayKey, assets}
        : {type: 'asset', path, displayKey, asset: assets[0]!};
    });
  }, [prefixPath, groups]);

  return (
    <div style={{overflow: 'hidden'}}>
      <Container ref={parentRef}>
        <VirtualizedAssetCatalogHeader headerCheckbox={headerCheckbox} view={view} />
        <Inner $totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            const row: Row = rows[index]!;
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
                checked={checkedDisplayKeys.has(row.displayKey)}
                onToggleChecked={onToggleFactory(row.displayKey)}
                onWipe={() => onWipe(wipeableAssets.map((a) => a.key))}
              />
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};
