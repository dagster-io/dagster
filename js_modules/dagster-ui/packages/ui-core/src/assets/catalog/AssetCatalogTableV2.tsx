import {
  Body,
  Box,
  Colors,
  Icon,
  MenuItem,
  NonIdealState,
  Popover,
  Select,
  Skeleton,
  Subtitle1,
  Tag,
  UnstyledButton,
  ifPlural,
} from '@dagster-io/ui-components';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {AssetCatalogAlerts} from 'shared/assets/catalog/AssetCatalogAlerts.oss';
import {AssetCatalogTabs} from 'shared/assets/catalog/AssetCatalogTabs.oss';
import {useCatalogExtraDropdownOptions} from 'shared/assets/catalog/useCatalogExtraDropdownOptions.oss';
import {AssetCatalogInsights} from 'shared/assets/insights/AssetCatalogInsights.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetCatalogAssetGraph} from './AssetCatalogAssetGraph';
import {
  AssetCatalogV2VirtualizedTable,
  AssetCatalogV2VirtualizedTableProps,
} from './AssetCatalogV2VirtualizedTable';
import {AssetHealthGroupBy, GROUP_BY_ITEMS} from './AttributeStatusHeaderRow';
import {SelectedAssetsPopoverContent} from './SelectedAssetsPopoverContent';
import {isHealthGroupBy, useAssetCatalogGroupAndSortBy} from './useAssetCatalogGroupAndSortBy';
import {useFullScreen} from '../../app/AppTopNav/AppTopNavContext';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {currentPageAtom, useTrackEvent} from '../../app/analytics';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {useAllAssets} from '../../assets/AssetsCatalogTable';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useSelectionReducer} from '../../hooks/useSelectionReducer';
import {useBlockTraceUntilTrue} from '../../performance/TraceContext';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../../ui/formatters';
import {AssetsEmptyState} from '../AssetsEmptyState';
import {LaunchAssetExecutionButton} from '../LaunchAssetExecutionButton';
import {asAssetKeyInput} from '../asInput';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

export const AssetCatalogTableV2 = React.memo(() => {
  const {assets, loading: assetsLoading, error} = useAllAssets();
  useBlockTraceUntilTrue('useAllAssets', !assetsLoading);
  const trackEvent = useTrackEvent();

  const {favorites, loading: favoritesLoading} = useFavoriteAssets();

  const penultimateAssets = useMemo(() => {
    if (!favorites) {
      return assets ?? [];
    }
    return (assets ?? []).filter((asset) => favorites.has(tokenForAssetKey(asset.key)));
  }, [favorites, assets]);

  const [errorState, setErrorState] = useState<SyntaxError[]>([]);

  const {
    filterInput,
    filtered,
    loading: selectionLoading,
    setAssetSelection,
    assetSelection,
  } = useAssetSelectionInput<AssetTableFragment>({
    assets: penultimateAssets,
    assetsLoading: !assets && (assetsLoading || favoritesLoading),
    onErrorStateChange: useCallback(
      (errors: SyntaxError[]) => {
        if (errors !== errorState) {
          setErrorState(errors);
        }
      },
      [errorState],
    ),
  });
  const loading = selectionLoading && !filtered.length;

  const {liveDataByNode} = useAssetsHealthData({
    assetKeys: useMemo(() => filtered.map((asset) => asAssetKeyInput(asset.key)), [filtered]),
    loading,
  });

  const healthDataLoading = useMemo(() => {
    return Object.values(liveDataByNode).length !== filtered.length;
  }, [liveDataByNode, filtered]);

  const {assetsByAssetKey: unfilteredAssetsByAssetKey} = useAllAssets();
  const filteredKeys = useMemo(
    () => new Set(filtered.map((asset) => tokenForAssetKey(asset.key))),
    [filtered],
  );
  const assetsByAssetKey = useMemo(() => {
    return new Map(
      Array.from(unfilteredAssetsByAssetKey.entries()).filter(([key]) => filteredKeys.has(key)),
    );
  }, [unfilteredAssetsByAssetKey, filteredKeys]);

  const {
    sortBy,
    setSortBy,
    groupBy,
    setGroupBy,
    groupedAndSorted,
    allGroups,
    SORT_ITEMS,
    ITEMS_BY_KEY,
  } = useAssetCatalogGroupAndSortBy({
    liveDataByNode,
    assetsByAssetKey,
  });

  const [selectedTab, setSelectedTab] = useQueryPersistedState<string>({
    queryKey: 'selectedTab',
    defaults: {selectedTab: 'assets'},
    decode: (qs) =>
      qs.selectedTab && typeof qs.selectedTab === 'string' ? qs.selectedTab : 'assets',
    encode: (b) => ({selectedTab: b || 'assets'}),
  });

  const displayKeys = useMemo(() => {
    return Object.values(groupedAndSorted).flatMap((group) =>
      group.assets.map((asset) => tokenForAssetKey(asset.key)),
    );
  }, [groupedAndSorted]);

  const [{checkedIds: checkedDisplayKeys}, {onToggleFactory}] = useSelectionReducer(displayKeys);

  const onToggleGroup = useCallback(
    (group: string) => {
      return (checked: boolean) => {
        groupedAndSorted[group]?.assets.forEach((asset) => {
          const toggle = onToggleFactory(tokenForAssetKey(asset.key));
          toggle({checked, shiftKey: false});
        });
      };
    },
    [groupedAndSorted, onToggleFactory],
  );

  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({
      specificPath,
      path: `${path}?view=AssetCatalogTableV2&selected_tab=${selectedTab}`,
    }));
  }, [path, setCurrentPage, selectedTab, trackEvent]);

  const onChangeTab = useCallback(
    (tab: string) => {
      setSelectedTab(tab);
      trackEvent('asset-selection-change-tab', {tab});
    },
    [setSelectedTab, trackEvent],
  );

  const {isFullScreen} = useFullScreen();

  const tabs = isFullScreen ? null : (
    <Box border="bottom" padding={{left: 24, right: 24}}>
      <AssetCatalogTabs onChangeTab={onChangeTab} selectedTab={selectedTab} />
    </Box>
  );

  const content = () => {
    if (error) {
      return <PythonErrorInfo error={error} />;
    }

    if (!assets?.length && !loading) {
      return (
        <Box padding={{vertical: 64}}>
          <AssetsEmptyState />
        </Box>
      );
    }
    if (favorites && filtered.length === 0 && !loading) {
      return (
        <Box padding={24}>
          <NonIdealState
            icon="star"
            title="No favorite assets"
            description="To add one, click the star in the asset view or choose 'Add to favorites' from the asset menu in the catalog."
          />
        </Box>
      );
    }
    switch (selectedTab) {
      case 'lineage':
        return (
          <AssetCatalogAssetGraph
            selection={assetSelection}
            onChangeSelection={setAssetSelection}
            tabs={tabs}
          />
        );
      case 'insights':
        return (
          <AssetCatalogInsights
            assets={filtered}
            selection={assetSelection}
            tabs={tabs}
            visibleSections={
              new Set(['rate-cards', 'performance-metrics', 'activity-charts', 'top-assets'])
            }
          />
        );
      case 'alerts':
        return <AssetCatalogAlerts tabs={tabs} selection={assetSelection} />;
      default:
        return (
          <Table
            assets={filtered}
            grouped={groupedAndSorted}
            loading={loading}
            selectionLoading={selectionLoading}
            healthDataLoading={healthDataLoading}
            tabs={tabs}
            sortBy={sortBy}
            setSortBy={setSortBy}
            groupBy={groupBy}
            setGroupBy={setGroupBy}
            checkedDisplayKeys={checkedDisplayKeys}
            onToggleFactory={onToggleFactory}
            onToggleGroup={onToggleGroup}
            allGroups={allGroups}
            SORT_ITEMS={SORT_ITEMS}
            ITEMS_BY_KEY={ITEMS_BY_KEY}
          />
        );
    }
  };

  const extraStyles =
    selectedTab === 'lineage'
      ? {
          gridTemplateColumns: 'minmax(500px, 1fr)',
          display: 'grid',
          gridTemplateRows: 'repeat(2, auto) minmax(0, 1fr)',
        }
      : {};
  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', minHeight: 600, ...extraStyles}}>
      <Box
        flex={{direction: 'row', alignItems: 'center', gap: 8}}
        padding={{vertical: 12, horizontal: 24}}
        border={['insights', 'lineage'].includes(selectedTab) ? 'bottom' : undefined}
      >
        <Box flex={{grow: 1, shrink: 1}}>{filterInput}</Box>
        <CreateCatalogViewButton />
      </Box>
      {/* Lineage and Insights render their own loading bars */}
      {content()}
    </Box>
  );
});

AssetCatalogTableV2.displayName = 'AssetCatalogTableV2';

type TableProps<T extends string, TAsset extends {key: {path: string[]}}> = {
  assets: AssetTableFragment[] | undefined;
  grouped: AssetCatalogV2VirtualizedTableProps<T, TAsset>['grouped'];
  loading: boolean;
  healthDataLoading: boolean;
  tabs: React.ReactNode;
  sortBy: ReturnType<typeof useAssetCatalogGroupAndSortBy>['sortBy'];
  setSortBy: ReturnType<typeof useAssetCatalogGroupAndSortBy>['setSortBy'];
  checkedDisplayKeys: Set<string>;
  onToggleFactory: (id: string) => (values: {checked: boolean; shiftKey: boolean}) => void;
  onToggleGroup: (group: T) => (checked: boolean) => void;
  selectionLoading: boolean;
  groupBy: AssetHealthGroupBy;
  setGroupBy: (groupBy: (typeof GROUP_BY_ITEMS)[number]['key']) => void;
  allGroups?: T[];
  SORT_ITEMS: ReturnType<typeof useAssetCatalogGroupAndSortBy>['SORT_ITEMS'];
  ITEMS_BY_KEY: ReturnType<typeof useAssetCatalogGroupAndSortBy>['ITEMS_BY_KEY'];
};

const Table = React.memo(
  <T extends string, TAsset extends {key: {path: string[]}}>({
    assets,
    grouped,
    loading,
    healthDataLoading,
    tabs,
    sortBy,
    setSortBy,
    checkedDisplayKeys,
    onToggleFactory,
    onToggleGroup,
    selectionLoading,
    groupBy,
    setGroupBy,
    allGroups: _allGroups,
    SORT_ITEMS,
    ITEMS_BY_KEY,
  }: TableProps<T, TAsset>) => {
    const scope = useMemo(() => {
      const selected = (assets ?? []).filter((a) =>
        checkedDisplayKeys.has(tokenForAssetKey(a.key)),
      );
      return {
        selected: selected.map((a) => ({...a.definition, assetKey: a.key})),
      };
    }, [assets, checkedDisplayKeys]);

    const extraDropdownOptions = useCatalogExtraDropdownOptions({scope});

    const allGroups = useMemo(() => {
      return _allGroups ?? (Object.keys(grouped) as T[]);
    }, [_allGroups, grouped]);

    return (
      <>
        <IndeterminateLoadingBar
          $loading={loading || (healthDataLoading && isHealthGroupBy(groupBy)) || selectionLoading}
        />
        {tabs}
        <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
          <Box
            flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
            padding={{horizontal: 24, vertical: 12}}
            border="bottom"
          >
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Subtitle1>
                {loading ? (
                  <Skeleton $width={200} $height={21} />
                ) : (
                  <>
                    {numberFormatter.format(assets?.length ?? 0)} asset
                    {ifPlural(assets?.length ?? 0, '', 's')}
                  </>
                )}
              </Subtitle1>
              {checkedDisplayKeys.size > 0 ? (
                <Popover
                  interactionKind="hover"
                  placement="bottom-start"
                  content={
                    <SelectedAssetsPopoverContent
                      checkedDisplayKeys={checkedDisplayKeys}
                      grouped={grouped}
                    />
                  }
                >
                  <Tag intent="primary">
                    {numberFormatter.format(checkedDisplayKeys.size)} selected
                  </Tag>
                </Popover>
              ) : null}
            </Box>
            <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <Body color={Colors.textLight()}>Group by</Body>
                <Select<(typeof GROUP_BY_ITEMS)[number]>
                  popoverProps={{
                    position: 'bottom-right',
                  }}
                  filterable={false}
                  activeItem={GROUP_BY_ITEMS.find((item) => item.key === groupBy)}
                  items={GROUP_BY_ITEMS}
                  itemRenderer={(item, props) => {
                    return (
                      <MenuItem
                        active={props.modifiers.active}
                        onClick={props.handleClick}
                        key={item.key}
                        icon={item.icon}
                        text={item.text}
                        style={{width: '300px'}}
                      />
                    );
                  }}
                  onItemSelect={(item) => setGroupBy(item.key)}
                >
                  <UnstyledButton $outlineOnHover style={{display: 'flex', padding: '6px 4px'}}>
                    {GROUP_BY_ITEMS.find((item) => item.key === groupBy)?.text}
                    <Icon name="arrow_drop_down" />
                  </UnstyledButton>
                </Select>
              </Box>
              <Box flex={{direction: 'row', alignItems: 'center', gap: 4}}>
                <Body color={Colors.textLight()}>Sort by</Body>
                <Select<(typeof SORT_ITEMS)[number]>
                  popoverProps={{
                    position: 'bottom-right',
                  }}
                  filterable={false}
                  activeItem={ITEMS_BY_KEY[sortBy]}
                  items={SORT_ITEMS}
                  itemRenderer={(item, props) => {
                    return (
                      <MenuItem
                        active={props.modifiers.active}
                        onClick={props.handleClick}
                        key={item.key}
                        text={item.text}
                        style={{width: '300px'}}
                      />
                    );
                  }}
                  onItemSelect={(item) => setSortBy(item.key)}
                >
                  <UnstyledButton $outlineOnHover style={{display: 'flex', padding: '6px 4px'}}>
                    {ITEMS_BY_KEY[sortBy].text}
                    <Icon name="arrow_drop_down" />
                  </UnstyledButton>
                </Select>
              </Box>
              {loading ? (
                <Skeleton $width={300} $height={21} />
              ) : (
                <LaunchAssetExecutionButton
                  scope={scope}
                  additionalDropdownOptions={extraDropdownOptions}
                />
              )}
            </Box>
          </Box>
          <div style={{flex: 1, overflow: 'hidden'}}>
            <AssetCatalogV2VirtualizedTable
              allGroups={allGroups}
              grouped={grouped}
              loading={loading}
              healthDataLoading={healthDataLoading}
              checkedDisplayKeys={checkedDisplayKeys}
              onToggleFactory={onToggleFactory}
              onToggleGroup={onToggleGroup}
              id={`asset-catalog-table-${groupBy}`}
            />
          </div>
        </Box>
      </>
    );
  },
);
Table.displayName = 'Table';
