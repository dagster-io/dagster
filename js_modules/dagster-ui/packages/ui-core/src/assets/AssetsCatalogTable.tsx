import {gql, useApolloClient} from '@apollo/client';
import {Box, ButtonGroup} from '@dagster-io/ui-components';
import * as React from 'react';
import {useCallback, useEffect, useLayoutEffect, useMemo, useState} from 'react';

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
} from './types/AssetsCatalogTable.types';
import {useAssetCatalogFiltering} from './useAssetCatalogFiltering';
import {AssetViewType, useAssetView} from './useAssetView';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {AssetGroupSelector} from '../graphql/types';
import {PageLoadTrace} from '../performance';
import {useIndexedDBCachedQuery} from '../search/useIndexedDBCachedQuery';
import {LoadingSpinner} from '../ui/Loading';
type Asset = AssetTableFragment;

const groupTableCache = new Map();

export function useAllAssets(groupSelector?: AssetGroupSelector) {
  const client = useApolloClient();
  const [{error, assets}, setErrorAndAssets] = useState<{
    error: PythonErrorFragment | undefined;
    assets: Asset[] | undefined;
  }>({error: undefined, assets: undefined});

  const assetsQuery = useIndexedDBCachedQuery<
    AssetCatalogTableQuery,
    AssetCatalogTableQueryVariables
  >({
    key: 'allAssets',
    query: ASSET_CATALOG_TABLE_QUERY,
    version: 1,
  });

  const {data, fetch: fetchAssets} = assetsQuery;

  const assetsOrError = data?.assetsOrError;
  useLayoutEffect(() => {
    if (assetsOrError) {
      setErrorAndAssets({
        error: assetsOrError?.__typename === 'PythonError' ? assetsOrError : undefined,
        assets: assetsOrError?.__typename === 'AssetConnection' ? assetsOrError.nodes : undefined,
      });
    }
  }, [assetsOrError]);

  const groupQuery = useCallback(async () => {
    if (!groupSelector) {
      return;
    }
    function onData(queryData: typeof data) {
      setErrorAndAssets({
        error: undefined,
        assets: queryData.assetNodes?.map(definitionToAssetTableFragment),
      });
    }
    const cacheKey = JSON.stringify(groupSelector);
    if (groupTableCache.has(cacheKey)) {
      onData(groupTableCache.get(cacheKey));
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
    onData(data);
  }, [groupSelector, client]);

  return useMemo(() => {
    return {
      assets,
      error,
      loading: !assets && !error,
      query: groupSelector ? groupQuery : fetchAssets,
    };
  }, [assets, error, fetchAssets, groupQuery, groupSelector]);
}

interface AssetCatalogTableProps {
  prefixPath: string[];
  setPrefixPath: (prefixPath: string[]) => void;
  groupSelector?: AssetGroupSelector;
  trace?: PageLoadTrace;
}

export const AssetsCatalogTable = ({
  prefixPath,
  setPrefixPath,
  groupSelector,
  trace,
}: AssetCatalogTableProps) => {
  const [view, setView] = useAssetView();

  const {assets, query, error} = useAllAssets(groupSelector);
  const {searchPath, filtered, isFiltered, filterButton, filterInput, activeFiltersJsx} =
    useAssetCatalogFiltering(assets, prefixPath);

  const {displayPathForAsset, displayed} =
    view === 'flat'
      ? buildFlatProps(filtered, prefixPath)
      : buildNamespaceProps(filtered, prefixPath);

  const refreshState = useRefreshAtInterval<any>({
    refresh: query,
    intervalMs: FIFTEEN_SECONDS,
    leading: true,
  });

  const loaded = !!assets;
  useEffect(() => {
    if (loaded) {
      trace?.endTrace();
    }
  }, [loaded, trace]);

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
      isFiltered={isFiltered}
      actionBarComponents={
        <>
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
          {filterButton}
          {filterInput}
        </>
      }
      belowActionBarComponents={
        activeFiltersJsx.length ? (
          <Box
            border="top-and-bottom"
            padding={{vertical: 12, left: 24, right: 12}}
            flex={{direction: 'row', gap: 4, alignItems: 'center'}}
          >
            {activeFiltersJsx}
          </Box>
        ) : null
      }
      refreshState={refreshState}
      prefixPath={prefixPath || []}
      searchPath={searchPath}
      displayPathForAsset={displayPathForAsset}
      requery={(_) => [{query: ASSET_CATALOG_TABLE_QUERY, fetchPolicy: 'no-cache'}]}
    />
  );
};

export const ASSET_CATALOG_TABLE_QUERY = gql`
  query AssetCatalogTableQuery {
    assetsOrError {
      ... on AssetConnection {
        nodes {
          id
          ...AssetTableFragment
        }
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
  // Return all assets from the next PAGE_SIZE namespaces - the AssetTable component will later
  // group them by namespace

  const namespaceForAsset = (asset: Asset) => {
    return asset.key.path.slice(prefixPath.length, prefixPath.length + 1);
  };

  // Only consider assets that start with the prefix path
  const assetsWithPathPrefix = assets.filter((asset) =>
    asset.key.path.join(',').startsWith(prefixPath.join(',')),
  );

  const namespaces = Array.from(
    new Set(assetsWithPathPrefix.map((asset) => JSON.stringify(namespaceForAsset(asset)))),
  )
    .map((x) => JSON.parse(x))
    .sort();

  return {
    displayPathForAsset: namespaceForAsset,
    displayed: filterAssetsByNamespace(
      assetsWithPathPrefix,
      namespaces.map((ns) => [...prefixPath, ...ns]),
    ),
  };
}

const filterAssetsByNamespace = (assets: Asset[], paths: string[][]) => {
  return assets.filter((asset) =>
    paths.some((path) => path.every((part, i) => part === asset.key.path[i])),
  );
};
