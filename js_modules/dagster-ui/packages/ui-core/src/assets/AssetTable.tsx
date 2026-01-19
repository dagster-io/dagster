import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  Menu,
  NonIdealState,
  Popover,
} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import * as React from 'react';
import {useMemo} from 'react';
import {useCatalogExtraDropdownOptions} from 'shared/assets/catalog/useCatalogExtraDropdownOptions.oss';

import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {AssetViewType} from './useAssetView';
import {RefetchQueriesFunction} from '../apollo-client';
import {useWipeMaterializations} from './useWipeMaterializations';
import {QueryRefreshCountdown, RefreshState} from '../app/QueryRefresh';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {InvalidSelectionQueryNotice} from '../pipelines/GraphNotices';
import {SyntaxError} from '../selection/CustomErrorListener';
import {VirtualizedAssetTable} from '../workspace/VirtualizedAssetTable';

type Asset = AssetTableFragment;

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
};

interface Props {
  view: AssetViewType;
  assets: Asset[];
  refreshState: RefreshState;
  actionBarComponents: React.ReactNode;
  belowActionBarComponents?: React.ReactNode;
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  assetSelection: string;
  isLoading: boolean;
  onChangeAssetSelection: (selection: string) => void;
  errorState?: SyntaxError[];
}

export const AssetTable = ({
  assets,
  actionBarComponents,
  belowActionBarComponents,
  refreshState,
  prefixPath,
  displayPathForAsset,
  assetSelection,
  view,
  isLoading,
  onChangeAssetSelection,
  errorState,
}: Props) => {
  const groupedByDisplayKey = useMemo(
    () => groupBy(assets, (a) => JSON.stringify(displayPathForAsset(a))),
    [assets, displayPathForAsset],
  );
  const displayKeys = useMemo(() => Object.keys(groupedByDisplayKey).sort(), [groupedByDisplayKey]);

  const [{checkedIds: checkedDisplayKeys}, {onToggleFactory, onToggleAll}] =
    useSelectionReducer(displayKeys);

  const checkedAssets = useMemo(() => {
    const assets: Asset[] = [];
    displayKeys.forEach((displayKey) => {
      if (checkedDisplayKeys.has(displayKey)) {
        groupedByDisplayKey[displayKey]?.forEach((asset) => {
          assets.push(asset);
        });
      }
    });
    return assets;
  }, [checkedDisplayKeys, displayKeys, groupedByDisplayKey]);

  const extraDropdownOptions = useCatalogExtraDropdownOptions(
    useMemo(
      () => ({
        scope: {selected: checkedAssets.map((a) => ({assetKey: a.key}))},
      }),
      [checkedAssets],
    ),
  );

  const content = () => {
    if (!assets.length && !isLoading) {
      if (errorState?.length) {
        return (
          <Box padding={{top: 64}}>
            <InvalidSelectionQueryNotice errors={errorState} />
          </Box>
        );
      }
      if (assetSelection) {
        return (
          <Box padding={{top: 64}}>
            <NonIdealState
              icon="search"
              title="没有匹配的资产"
              description={
                <div>
                  未找到匹配 <strong>{assetSelection}</strong> 的资产
                </div>
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState icon="search" title="暂无资产" description="未找到任何资产" />
        </Box>
      );
    }

    return (
      <VirtualizedAssetTable
        headerCheckbox={
          <Checkbox
            indeterminate={
              checkedDisplayKeys.size > 0 && checkedDisplayKeys.size !== displayKeys.length
            }
            checked={checkedDisplayKeys.size > 0 && checkedDisplayKeys.size === displayKeys.length}
            onChange={(e) => {
              if (e.target instanceof HTMLInputElement) {
                onToggleAll(checkedDisplayKeys.size !== displayKeys.length);
              }
            }}
          />
        }
        prefixPath={prefixPath}
        groups={groupedByDisplayKey}
        checkedDisplayKeys={checkedDisplayKeys}
        onToggleFactory={onToggleFactory}
        onRefresh={() => refreshState.refetch()}
        showRepoColumn
        view={view}
        isLoading={isLoading}
        onChangeAssetSelection={onChangeAssetSelection}
      />
    );
  };

  return (
    <>
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <div
          style={{
            padding: '12px 24px',
            position: 'sticky',
            top: 0,
            zIndex: 1,
            background: Colors.backgroundDefault(),
            alignItems: 'flex-start',
            gap: 12,
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1fr) auto',
          }}
        >
          <div>{actionBarComponents}</div>
          <Box
            style={{justifySelf: 'flex-end'}}
            flex={{gap: 12, direction: 'row-reverse', alignItems: 'center'}}
          >
            <QueryRefreshCountdown refreshState={refreshState} />
            <Box flex={{alignItems: 'center', gap: 8}}>
              <LaunchAssetExecutionButton
                scope={{
                  selected: checkedAssets
                    .filter((a): a is AssetWithDefinition => !!a.definition)
                    .map((a) => ({...a.definition, assetKey: a.key})),
                }}
                additionalDropdownOptions={extraDropdownOptions}
              />
              <MoreActionsDropdown
                selected={checkedAssets}
                clearSelection={() => onToggleAll(false)}
              />
            </Box>
          </Box>
        </div>
        {belowActionBarComponents}
        {content()}
      </Box>
    </>
  );
};

interface MoreActionsDropdownProps {
  selected: Asset[];
  clearSelection: () => void;
  requery?: RefetchQueriesFunction;
}

const MoreActionsDropdown = React.memo((props: MoreActionsDropdownProps) => {
  const {selected, clearSelection, requery} = props;

  const {menuItem, dialog} = useWipeMaterializations({
    selected,
    onComplete: clearSelection,
    requery,
  });

  return (
    <>
      <Popover position="bottom-right" content={<Menu>{menuItem}</Menu>}>
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
      {dialog}
    </>
  );
});
