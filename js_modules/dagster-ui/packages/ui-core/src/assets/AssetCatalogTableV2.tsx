import {Box, Skeleton, Subtitle1, Tab, Tabs, ifPlural} from '@dagster-io/ui-components';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import updateLocale from 'dayjs/plugin/updateLocale';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetCatalogAssetGraph} from './AssetCatalogAssetGraph';
import {AssetCatalogV2VirtualizedTable} from './AssetCatalogV2VirtualizedTable';
import {AssetHealthStatusString, statusToIconAndColor} from './AssetHealthSummary';
import {useAllAssets} from './AssetsCatalogTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {asAssetKeyInput} from './asInput';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {currentPageAtom} from '../app/analytics';
import {useAssetsHealthData} from '../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../asset-data/types/AssetHealthDataProvider.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetSelectionInput} from '../asset-selection/input/useAssetSelectionInput';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {SyntaxError} from '../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {numberFormatter} from '../ui/formatters';
dayjs.extend(relativeTime);
dayjs.extend(updateLocale);

export const AssetsCatalogTableV2 = React.memo(
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
    const {filterInput, filtered, loading, setAssetSelection, assetSelection} =
      useAssetSelectionInput<AssetTableFragment>({
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
        const status = statusToIconAndColor[asset.assetHealth?.assetHealth ?? 'undefined'].text;
        byStatus[status].push(asset);
      });
      return byStatus;
    }, [liveDataByNode]);

    const [selectedTab, setSelectedTab] = useQueryPersistedState<string | undefined>({
      queryKey: 'selectedTab',
      decode: (qs) =>
        qs.selectedTab && typeof qs.selectedTab === 'string' ? qs.selectedTab : undefined,
      encode: (b) => ({selectedTab: b || undefined}),
    });

    const setCurrentPage = useSetRecoilState(currentPageAtom);
    const {path} = useRouteMatch();
    useEffect(() => {
      setCurrentPage(({specificPath}) => ({
        specificPath,
        path: `${path}?view=AssetCatalogTableV2&selected_tab=${selectedTab}`,
      }));
    }, [path, setCurrentPage, selectedTab]);

    const content = useMemo(() => {
      switch (selectedTab) {
        case 'lineage':
          return (
            <AssetCatalogAssetGraph
              selection={assetSelection}
              onChangeSelection={setAssetSelection}
              isFullScreen={isFullScreen}
              toggleFullScreen={toggleFullScreen}
            />
          );
        case 'insights':
          return <div>Insights</div>;
        default:
          return <Table assets={filtered} groupedByStatus={groupedByStatus} loading={loading} />;
      }
    }, [
      selectedTab,
      filtered,
      groupedByStatus,
      loading,
      assetSelection,
      setAssetSelection,
      isFullScreen,
      toggleFullScreen,
    ]);

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

    return (
      <Box flex={{direction: 'column'}} style={{height: '100%', minHeight: 600}}>
        <Box
          flex={{direction: 'row', alignItems: 'center', gap: 8}}
          padding={{vertical: 12, horizontal: 24}}
          border="bottom"
        >
          <Box flex={{grow: 1, shrink: 1}}>{filterInput}</Box>
          <CreateCatalogViewButton />
        </Box>
        {selectedTab === 'catalog' ? (
          <IndeterminateLoadingBar $loading={loading || healthDataLoading} />
        ) : null}
        <Box border="bottom">
          {isFullScreen ? null : (
            <Tabs
              onChange={setSelectedTab}
              selectedTabId={selectedTab}
              style={{marginLeft: 24, marginRight: 24}}
            >
              <Tab id="catalog" title="Catalog" />
              <Tab id="lineage" title="Lineage" />
              <Tab id="insights" title="Insights" />
            </Tabs>
          )}
        </Box>
        {content}
      </Box>
    );
  },
);

const Table = React.memo(
  ({
    assets,
    groupedByStatus,
    loading,
  }: {
    assets: AssetTableFragment[] | undefined;
    groupedByStatus: Record<AssetHealthStatusString, AssetHealthFragment[]>;
    loading: boolean;
  }) => {
    const scope = useMemo(
      () => ({
        all: (assets ?? [])
          .filter((a): a is AssetWithDefinition => !!a.definition)
          .map((a) => ({...a.definition, assetKey: a.key})),
      }),
      [assets],
    );

    // console.log({groupedByStatus, loading});

    return (
      <div style={{display: 'grid', gridTemplateRows: 'minmax(0, 1fr)', height: '100%'}}>
        <div
        // style={{
        //   display: 'grid',
        //   gridTemplateColumns: 'minmax(0, 1fr) 374px',
        //   height: '100%',
        // }}
        >
          <div
            style={{display: 'grid', gridTemplateRows: 'auto minmax(500px, 1fr)', height: '100%'}}
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
              {loading ? (
                <Skeleton $width={300} $height={21} />
              ) : (
                <LaunchAssetExecutionButton primary={false} scope={scope} />
              )}
            </Box>
            <AssetCatalogV2VirtualizedTable groupedByStatus={groupedByStatus} loading={loading} />
          </div>
          {/* <Box border="left" padding={{vertical: 24, horizontal: 12}}>
            Sidebar
          </Box> */}
        </div>
      </div>
    );
  },
);

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
};
