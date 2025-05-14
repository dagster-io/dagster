import {
  Body,
  Box,
  Colors,
  Icon,
  MenuItem,
  NonIdealState,
  Select,
  Skeleton,
  Subtitle1,
  Tab,
  Tabs,
  UnstyledButton,
  ifPlural,
} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import updateLocale from 'dayjs/plugin/updateLocale';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {AssetCatalogInsights} from 'shared/assets/insights/AssetCatalogInsights.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetCatalogAssetGraph} from './AssetCatalogAssetGraph';
import {AssetCatalogV2VirtualizedTable} from './AssetCatalogV2VirtualizedTable';
import {PythonErrorInfo} from '../../app/PythonErrorInfo';
import {COMMON_COLLATOR, assertUnreachable} from '../../app/Util';
import {currentPageAtom} from '../../app/analytics';
import {usePrefixedCacheKey} from '../../app/usePrefixedCacheKey';
import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {useAllAssets} from '../../assets/AssetsCatalogTable';
import {AssetHealthStatus} from '../../graphql/types';
import {useQueryPersistedState} from '../../hooks/useQueryPersistedState';
import {useStateWithStorage} from '../../hooks/useStateWithStorage';
import {useBlockTraceUntilTrue} from '../../performance/TraceContext';
import {SyntaxError} from '../../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../../ui/formatters';
import {AssetHealthStatusString, statusToIconAndColor} from '../AssetHealthSummary';
import {AssetsEmptyState} from '../AssetsEmptyState';
import {LaunchAssetExecutionButton} from '../LaunchAssetExecutionButton';
import {asAssetKeyInput} from '../asInput';
import {AssetTableFragment} from '../types/AssetTableFragment.types';

dayjs.extend(relativeTime);
dayjs.extend(updateLocale);

export const AssetCatalogTableV2 = React.memo(
  ({isFullScreen, toggleFullScreen}: {isFullScreen: boolean; toggleFullScreen: () => void}) => {
    const {assets, loading: assetsLoading, error} = useAllAssets();
    useBlockTraceUntilTrue('useAllAssets', !!assets?.length && !assetsLoading);

    const {favorites, loading: favoritesLoading} = useFavoriteAssets();

    const penultimateAssets = useMemo(() => {
      if (!favorites) {
        return assets ?? [];
      }
      return (assets ?? []).filter((asset: AssetTableFragment) =>
        favorites.has(tokenForAssetKey(asset.key)),
      );
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

    const [sortBy, setSortBy] = useStateWithStorage<(typeof SORT_ITEMS)[number]['key']>(
      usePrefixedCacheKey('catalog-sortBy'),
      (json) => {
        if (['materialization_asc', 'materialization_desc', 'key_asc', 'key_desc'].includes(json)) {
          return json;
        }
        return 'materialization_asc';
      },
    );

    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => filtered.map((asset) => asAssetKeyInput(asset.key)), [filtered]),
    );

    const healthDataLoading = useMemo(() => {
      return Object.values(liveDataByNode).length !== filtered.length;
    }, [liveDataByNode, filtered]);

    const groupedByStatus = useMemo(() => {
      const byStatus: Record<AssetHealthStatusString, (typeof liveDataByNode)[string][]> = {
        Degraded: [],
        Warning: [],
        Healthy: [],
        Unknown: [],
      };
      Object.values(liveDataByNode).forEach((asset) => {
        const status =
          statusToIconAndColor[asset.assetHealth?.assetHealth ?? AssetHealthStatus.UNKNOWN].text;
        byStatus[status].push(asset);
      });
      let sortFn;
      switch (sortBy) {
        case 'materialization_asc':
          sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
            sortAssetsByMaterializationTimestamp(a, b);
          break;
        case 'materialization_desc':
          sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
            sortAssetsByMaterializationTimestamp(b, a);
          break;
        case 'key_asc':
          sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
            COMMON_COLLATOR.compare(tokenForAssetKey(a.key), tokenForAssetKey(b.key));
          break;
        case 'key_desc':
          sortFn = (a: AssetHealthFragment, b: AssetHealthFragment) =>
            COMMON_COLLATOR.compare(tokenForAssetKey(b.key), tokenForAssetKey(a.key));
          break;
        default:
          assertUnreachable(sortBy);
      }
      Object.values(byStatus).forEach((assets) => {
        assets.sort(sortFn);
      });
      return byStatus;
    }, [liveDataByNode, sortBy]);

    const [selectedTab, setSelectedTab] = useQueryPersistedState<string>({
      queryKey: 'selectedTab',
      defaults: {selectedTab: 'assets'},
      decode: (qs) =>
        qs.selectedTab && typeof qs.selectedTab === 'string' ? qs.selectedTab : 'assets',
      encode: (b) => ({selectedTab: b || 'assets'}),
    });

    const setCurrentPage = useSetRecoilState(currentPageAtom);
    const {path} = useRouteMatch();
    useEffect(() => {
      setCurrentPage(({specificPath}) => ({
        specificPath,
        path: `${path}?view=AssetCatalogTableV2&selected_tab=${selectedTab}`,
      }));
    }, [path, setCurrentPage, selectedTab]);

    const tabs = useMemo(
      () => (
        <Box border="bottom">
          {isFullScreen ? null : (
            <Tabs
              onChange={setSelectedTab}
              selectedTabId={selectedTab}
              style={{marginLeft: 24, marginRight: 24}}
            >
              <Tab id="assets" title="Assets" />
              <Tab id="lineage" title="Lineage" />
              <Tab id="insights" title="Insights" />
            </Tabs>
          )}
        </Box>
      ),
      [isFullScreen, selectedTab, setSelectedTab],
    );

    const content = useMemo(() => {
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
              isFullScreen={isFullScreen}
              toggleFullScreen={toggleFullScreen}
              tabs={tabs}
            />
          );
        case 'insights':
          return <AssetCatalogInsights assets={filtered} selection={assetSelection} tabs={tabs} />;
        default:
          return (
            <Table
              assets={filtered}
              groupedByStatus={groupedByStatus}
              loading={loading}
              healthDataLoading={healthDataLoading}
              tabs={tabs}
              sortBy={sortBy}
              setSortBy={setSortBy}
            />
          );
      }
    }, [
      error,
      assets?.length,
      loading,
      selectedTab,
      assetSelection,
      setAssetSelection,
      isFullScreen,
      toggleFullScreen,
      filtered,
      groupedByStatus,
      favorites,
      healthDataLoading,
      tabs,
      sortBy,
      setSortBy,
    ]);

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
        {content}
      </Box>
    );
  },
);

AssetCatalogTableV2.displayName = 'AssetCatalogTableV2';

const SORT_ITEMS = [
  {
    key: 'materialization_asc' as const,
    text: 'Materialization (asc)',
  },
  {
    key: 'materialization_desc' as const,
    text: 'Materialization (desc)',
  },
  {
    key: 'key_asc' as const,
    text: 'Asset key (asc)',
  },
  {
    key: 'key_desc' as const,
    text: 'Asset key (desc)',
  },
];
const ITEMS_BY_KEY = SORT_ITEMS.reduce(
  (acc, item) => {
    acc[item.key] = item;
    return acc;
  },
  {} as Record<(typeof SORT_ITEMS)[number]['key'], (typeof SORT_ITEMS)[number]>,
);

const Table = React.memo(
  ({
    assets,
    groupedByStatus,
    loading,
    healthDataLoading,
    tabs,
    sortBy,
    setSortBy,
  }: {
    assets: AssetTableFragment[] | undefined;
    groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
    loading: boolean;
    healthDataLoading: boolean;
    tabs: React.ReactNode;
    sortBy: (typeof SORT_ITEMS)[number]['key'];
    setSortBy: (sortBy: (typeof SORT_ITEMS)[number]['key']) => void;
  }) => {
    const scope = useMemo(
      () => ({
        all: (assets ?? [])
          .filter((a): a is AssetWithDefinition => !!a.definition)
          .map((a) => ({...a.definition, assetKey: a.key})),
      }),
      [assets],
    );
    return (
      <>
        <IndeterminateLoadingBar $loading={loading || healthDataLoading} />
        {tabs}
        <div
          style={{
            display: 'grid',
            gridTemplateRows: 'minmax(0, 1fr)',
            height: 'calc(100% - 108px)', // TODO: temporary hack to account for top section. Will redo this rendering logic
          }}
        >
          <div
          // style={{
          //   display: 'grid',
          //   gridTemplateColumns: 'minmax(0, 1fr) 374px',
          //   height: '100%',
          // }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateRows: 'auto minmax(500px, 1fr)',
                height: '100%',
                gridTemplateColumns: 'minmax(500px, 1fr)',
              }}
            >
              <Box
                flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
                padding={{horizontal: 24, vertical: 12}}
                border="bottom"
              >
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
                <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
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
                    <LaunchAssetExecutionButton scope={scope} />
                  )}
                </Box>
              </Box>
              <AssetCatalogV2VirtualizedTable
                groupedByStatus={groupedByStatus}
                loading={loading}
                healthDataLoading={healthDataLoading}
              />
            </div>
          </div>
        </div>
      </>
    );
  },
);
Table.displayName = 'Table';

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
};

function sortAssetsByMaterializationTimestamp(a: AssetHealthFragment, b: AssetHealthFragment) {
  const aMaterialization = a.assetMaterializations[0]?.timestamp;
  const bMaterialization = b.assetMaterializations[0]?.timestamp;
  if (!aMaterialization && !bMaterialization) {
    return 0;
  }
  if (!aMaterialization) {
    return 1;
  }
  if (!bMaterialization) {
    return -1;
  }
  return Number(bMaterialization) - Number(aMaterialization);
}
