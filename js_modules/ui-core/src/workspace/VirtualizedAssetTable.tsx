import {Container, Inner} from '@dagster-io/ui-components';
import {useVirtualizer} from '@tanstack/react-virtual';
import * as React from 'react';

import {
  ShimmerRow,
  VirtualizedAssetCatalogHeader,
  VirtualizedAssetRow,
} from './VirtualizedAssetRow';
import {buildRepoAddress} from './buildRepoAddress';
import {LayoutContext} from '../app/LayoutProvider';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetTableFragment} from '../assets/types/AssetTableFragment.types';
import {AssetViewType} from '../assets/useAssetView';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';

// Keep in sync with the mobile card layout in css/VirtualizedAssetRow.module.css.
const MOBILE_ROW_HEIGHT = 60;

type Row =
  | {type: 'asset'; path: string[]; displayKey: string; asset: AssetTableFragment}
  | {type: 'folder'; path: string[]; displayKey: string; assets: AssetTableFragment[]}
  | {type: 'shimmer'};

interface Props {
  headerCheckbox: React.ReactNode;
  prefixPath: string[];
  groups: {[displayKey: string]: AssetTableFragment[]};
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (path: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onRefresh: () => void;
  showRepoColumn: boolean;
  // Defaults to true; the phone catalog hides checkboxes until "Select" is on.
  showCheckboxColumn?: boolean;
  view?: AssetViewType;
  isLoading?: boolean;
  onChangeAssetSelection?: (selection: string) => void;
}

export const VirtualizedAssetTable = (props: Props) => {
  const {
    headerCheckbox,
    prefixPath,
    groups,
    checkedDisplayKeys,
    onToggleFactory,
    onRefresh,
    showRepoColumn,
    showCheckboxColumn = true,
    view = 'flat',
    isLoading,
    onChangeAssetSelection,
  } = props;
  const parentRef = React.useRef<HTMLDivElement | null>(null);

  const rows: Row[] = React.useMemo(() => {
    if (isLoading && !Object.keys(groups).length) {
      return new Array(5).fill({type: 'shimmer'});
    }
    return Object.entries(groups).map(([displayKey, assets]) => {
      const path = [...prefixPath, ...JSON.parse(displayKey)];
      const isFolder =
        assets.length > 1 ||
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        tokenForAssetKey({path}) !== tokenForAssetKey(assets[0]!.key);
      return isFolder
        ? {type: 'folder', path, displayKey, assets}
        : // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          {type: 'asset', path, displayKey, asset: assets[0]!};
    });
  }, [prefixPath, groups, isLoading]);

  // The row stacks into a card below MOBILE_BREAKPOINT_PX (see
  // css/VirtualizedAssetRow.module.css), and its height then depends on the
  // content — status, kind tags, partition counts, freshness timers. A fixed
  // height clips whichever asset happens to carry the most metadata, so mobile
  // measures each row instead.
  const {isMobileScreen} = React.useContext(LayoutContext).nav;

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => (isMobileScreen ? MOBILE_ROW_HEIGHT : 64),
    overscan: 5,
  });

  const totalHeight = rowVirtualizer.getTotalSize();
  const items = rowVirtualizer.getVirtualItems();

  return (
    <div style={{overflow: 'hidden'}}>
      <IndeterminateLoadingBar $loading={isLoading} />
      <Container ref={parentRef}>
        <VirtualizedAssetCatalogHeader headerCheckbox={headerCheckbox} view={view} />
        <Inner totalHeight={totalHeight}>
          {items.map(({index, key, size, start}) => {
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            const row: Row = rows[index]!;
            if (row.type === 'shimmer') {
              return (
                <ShimmerRow
                  key={index}
                  $height={size}
                  $start={start}
                  $showRepoColumn={showRepoColumn}
                />
              );
            }

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

            return (
              <VirtualizedAssetRow
                key={key}
                view={view}
                type={rowType()}
                path={row.path}
                definition={row.type === 'asset' ? row.asset.definition : null}
                repoAddress={repoAddress()}
                showCheckboxColumn={showCheckboxColumn}
                showRepoColumn={showRepoColumn}
                height={isMobileScreen ? undefined : size}
                start={start}
                measureRef={isMobileScreen ? rowVirtualizer.measureElement : undefined}
                dataIndex={index}
                checked={checkedDisplayKeys.has(row.displayKey)}
                onToggleChecked={onToggleFactory(row.displayKey)}
                onRefresh={onRefresh}
                onChangeAssetSelection={onChangeAssetSelection}
              />
            );
          })}
        </Inner>
      </Container>
    </div>
  );
};
