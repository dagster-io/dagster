import {Box, ButtonGroup} from '@dagster-io/ui-components';
import * as React from 'react';
import {useCallback, useContext, useEffect, useLayoutEffect, useMemo, useState} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {CreateCatalogViewButton} from 'shared/assets/CreateCatalogViewButton.oss';
import {useFavoriteAssets} from 'shared/assets/useFavoriteAssets.oss';

import {AssetTable} from './AssetTable';
import {ASSET_TABLE_DEFINITION_FRAGMENT, ASSET_TABLE_FRAGMENT} from './AssetTableFragment';
import {AssetsEmptyState} from './AssetsEmptyState';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {
  AssetCatalogGroupTableNodeFragment,
  AssetCatalogGroupTableQuery,
  AssetCatalogGroupTableQueryVariables,
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
  AssetCatalogTableQueryVersion,
} from './types/AssetsCatalogTable.types';
import {AssetViewType, useAssetView} from './useAssetView';
import {gql, useApolloClient} from '../apollo-client';
import {AppContext} from '../app/AppContext';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {currentPageAtom} from '../app/analytics';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetSelectionInput} from '../asset-selection/input/useAssetSelectionInput';
import {getAssetsByKey} from '../asset-selection/util';
import {AssetGroupSelector} from '../graphql/types';
import {useUpdatingRef} from '../hooks/useUpdatingRef';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {fetchPaginatedData} from '../runs/fetchPaginatedBucketData';
import {getCacheManager} from '../search/useIndexedDBCachedQuery';
import {SyntaxError} from '../selection/CustomErrorListener';
import {LoadingSpinner} from '../ui/Loading';

type Asset = AssetTableFragment;

const groupTableCache = new Map();
const emptyArray: string[] = [];

const DEFAULT_BATCH_LIMIT = 10000;

export function useCachedAssets({
  onAssetsLoaded,
}: {
  onAssetsLoaded: (data: AssetTableFragment[]) => void;
}) {
  const {localCacheIdPrefix} = useContext(AppContext);
  const cacheManager = useMemo(
    () => getCacheManager<AssetTableFragment[]>(`${localCacheIdPrefix}/allAssetNodes`),
    [localCacheIdPrefix],
  );

  useLayoutEffect(() => {
    cacheManager.get(AssetCatalogTableQueryVersion).then((data) => {
      if (data) {
        onAssetsLoaded(data);
      }
    });
  }, [cacheManager, onAssetsLoaded]);

  return {cacheManager};
}

// Module-level cache variables
let globalAssetsPromise: Promise<Asset[]> | null = null;
let cachedAllAssets: Asset[] | null = null;
let cachedAssetsFetchTime: number = 0;

export function useAllAssets({
  batchLimit = DEFAULT_BATCH_LIMIT,
  groupSelector,
}: {groupSelector?: AssetGroupSelector; batchLimit?: number} = {}) {
  const client = useApolloClient();
  const [{error, assets}, setErrorAndAssets] = useState<{
    error: PythonErrorFragment | undefined;
    assets: Asset[] | undefined;
  }>({error: undefined, assets: cachedAllAssets || undefined});

  const assetsRef = useUpdatingRef(assets);

  const {cacheManager} = useCachedAssets({
    onAssetsLoaded: useCallback(
      (data) => {
        if (!assetsRef.current) {
          setErrorAndAssets({
            error: undefined,
            assets: data,
          });
        }
      },
      [assetsRef],
    ),
  });

  // Query function for all assets
  const fetchAllAssets = useCallback(async () => {
    if (cachedAllAssets && Date.now() - cachedAssetsFetchTime < 6000) {
      return cachedAllAssets;
    }
    if (!globalAssetsPromise) {
      globalAssetsPromise = (async () => {
        const allAssets = await fetchPaginatedData({
          async fetchData(cursor: string | null | undefined) {
            const {data} = await client.query<
              AssetCatalogTableQuery,
              AssetCatalogTableQueryVariables
            >({
              query: ASSET_CATALOG_TABLE_QUERY,
              fetchPolicy: 'no-cache',
              variables: {cursor, limit: batchLimit},
            });
            if (data.assetsOrError.__typename === 'PythonError') {
              return {
                data: [],
                cursor: undefined,
                hasMore: false,
                error: data.assetsOrError,
              };
            }
            const assets = data.assetsOrError.nodes;
            const hasMoreData = assets.length === batchLimit;
            const nextCursor = data.assetsOrError.cursor;
            return {data: assets, cursor: nextCursor, hasMore: hasMoreData, error: undefined};
          },
        });
        cachedAssetsFetchTime = Date.now();
        cachedAllAssets = allAssets;
        cacheManager.set(allAssets, AssetCatalogTableQueryVersion);
        globalAssetsPromise = null;
        return allAssets;
      })();
    }
    return globalAssetsPromise;
  }, [batchLimit, cacheManager, client]);

  // Query function for group assets
  const groupQuery = useCallback(async () => {
    const cacheKey = JSON.stringify(groupSelector);
    if (groupTableCache.has(cacheKey)) {
      const cachedData = groupTableCache.get(cacheKey);
      setErrorAndAssets({
        error: undefined,
        assets: cachedData.assetNodes?.map(definitionToAssetTableFragment),
      });
      return;
    }
    const {data} = await client.query<
      AssetCatalogGroupTableQuery,
      AssetCatalogGroupTableQueryVariables
    >({
      query: ASSET_CATALOG_GROUP_TABLE_QUERY,
      variables: {group: groupSelector},
      fetchPolicy: 'no-cache',
    });
    groupTableCache.set(cacheKey, data);
    setErrorAndAssets({
      error: undefined,
      assets: data.assetNodes?.map(definitionToAssetTableFragment),
    });
  }, [client, groupSelector]);

  const query = groupSelector ? groupQuery : fetchAllAssets;

  useEffect(() => {
    if (groupSelector) {
      groupQuery();
    } else {
      fetchAllAssets()
        .then((allAssets) => setErrorAndAssets({error: undefined, assets: allAssets}))
        .catch((e: any) => {
          if (e.__typename === 'PythonError') {
            setErrorAndAssets((prev) => ({error: e, assets: prev.assets}));
          }
        });
    }
  }, [fetchAllAssets, groupQuery, groupSelector]);

  return useMemo(
    () => ({
      assets,
      assetsByAssetKey: getAssetsByKey(assets ?? []),
      error,
      loading: !assets && !error,
      query,
    }),
    [assets, error, query],
  );
}

interface AssetCatalogTableProps {
  prefixPath: string[];
  setPrefixPath: (prefixPath: string[]) => void;
  groupSelector?: AssetGroupSelector;
}

export const AssetsCatalogTable = ({
  prefixPath,
  setPrefixPath,
  groupSelector,
}: AssetCatalogTableProps) => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path: `${path}?view=AssetCatalogTable`}));
  }, [path, setCurrentPage]);

  const [view, setView] = useAssetView();

  const {assets, loading: assetsLoading, query, error} = useAllAssets({groupSelector});

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
  const {filterInput, filtered, loading, assetSelection, setAssetSelection} =
    useAssetSelectionInput({
      assets: penultimateAssets,
      assetsLoading: !assets || assetsLoading || favoritesLoading,
      onErrorStateChange: (errors) => {
        if (errors !== errorState) {
          setErrorState(errors);
        }
      },
    });

  useBlockTraceUntilTrue('useAllAssets', !!assets?.length && !loading);

  const {displayPathForAsset, displayed} = useMemo(
    () =>
      view === 'flat'
        ? buildFlatProps(filtered as AssetTableFragment[], prefixPath)
        : buildNamespaceProps(filtered as AssetTableFragment[], prefixPath),
    [filtered, prefixPath, view],
  );

  const refreshState = useRefreshAtInterval<any>({
    refresh: query,
    intervalMs: 4 * FIFTEEN_SECONDS,
    leading: true,
  });

  React.useEffect(() => {
    if (view !== 'directory' && prefixPath.length) {
      setView('directory');
    }
  }, [view, setView, prefixPath]);

  if (error) {
    return <PythonErrorInfo error={error} />;
  }

  if (!assets) {
    return <LoadingSpinner purpose="page" />;
  }

  if (!assets.length) {
    return (
      <Box padding={{vertical: 64}}>
        <AssetsEmptyState prefixPath={prefixPath} />
      </Box>
    );
  }

  return (
    <AssetTable
      view={view}
      assets={displayed}
      isLoading={loading}
      errorState={errorState}
      actionBarComponents={
        <Box flex={{gap: 12, alignItems: 'flex-start'}}>
          <ButtonGroup<AssetViewType>
            activeItems={new Set([view])}
            buttons={[
              {id: 'flat', icon: 'view_list', tooltip: 'List view'},
              {id: 'directory', icon: 'folder', tooltip: 'Folder view'},
            ]}
            onClick={(view) => {
              setView(view);
              if (view === 'flat' && prefixPath.length) {
                setPrefixPath([]);
              }
            }}
          />
          {filterInput}
          <CreateCatalogViewButton />
        </Box>
      }
      refreshState={refreshState}
      prefixPath={prefixPath || emptyArray}
      assetSelection={assetSelection}
      displayPathForAsset={displayPathForAsset}
      onChangeAssetSelection={setAssetSelection}
    />
  );
};

export const ASSET_CATALOG_TABLE_QUERY = gql`
  query AssetCatalogTableQuery($cursor: String, $limit: Int!) {
    assetsOrError(cursor: $cursor, limit: $limit) {
      ... on AssetConnection {
        nodes {
          id
          ...AssetTableFragment
        }
        cursor
      }
      ...PythonErrorFragment
    }
  }

  ${ASSET_TABLE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const ASSET_CATALOG_GROUP_TABLE_QUERY = gql`
  query AssetCatalogGroupTableQuery($group: AssetGroupSelector) {
    assetNodes(group: $group) {
      id
      ...AssetCatalogGroupTableNode
    }
  }

  fragment AssetCatalogGroupTableNode on AssetNode {
    id
    assetKey {
      path
    }
    ...AssetTableDefinitionFragment
  }

  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

// When we load the AssetCatalogTable for a particular asset group, we retrieve `assetNodes`,
// not `assets`. To narrow the scope of this difference we coerce the nodes to look like
// AssetCatalogTableQuery results.
function definitionToAssetTableFragment(definition: AssetCatalogGroupTableNodeFragment): Asset {
  return {__typename: 'Asset', id: definition.id, key: definition.assetKey, definition};
}

function buildFlatProps(assets: Asset[], _: string[]) {
  return {
    displayed: assets,
    displayPathForAsset: (asset: Asset) => asset.key.path,
  };
}

function buildNamespaceProps(assets: Asset[], prefixPath: string[]) {
  // Return all assets matching prefixPath - the AssetTable component will later
  // group them by namespace

  const namespaceForAsset = (asset: Asset) => {
    return asset.key.path.slice(prefixPath.length, prefixPath.length + 1);
  };

  const assetsWithPathPrefix = assets.filter((asset) =>
    prefixPath.every((part, index) => part === asset.key.path[index]),
  );

  return {
    displayPathForAsset: namespaceForAsset,
    displayed: assetsWithPathPrefix,
  };
}
