import {gql, QueryResult, useQuery} from '@apollo/client';
import {Box, TextInput, ButtonGroup} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {AssetGroupSelector} from '../graphql/types';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {useStartTrace} from '../performance';
import {LoadingSpinner} from '../ui/Loading';

import {
  AssetGroupSuggest,
  buildAssetGroupSelector,
  useAssetGroupSelectorsForAssets,
} from './AssetGroupSuggest';
import {AssetTable} from './AssetTable';
import {ASSET_TABLE_DEFINITION_FRAGMENT, ASSET_TABLE_FRAGMENT} from './AssetTableFragment';
import {AssetsEmptyState} from './AssetsEmptyState';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
  AssetCatalogGroupTableQuery,
  AssetCatalogGroupTableNodeFragment,
  AssetCatalogGroupTableQueryVariables,
} from './types/AssetsCatalogTable.types';
import {useAssetSearch} from './useAssetSearch';
import {AssetViewType, useAssetView} from './useAssetView';

type Asset = AssetTableFragment;

function useAllAssets(groupSelector?: AssetGroupSelector): {
  query: QueryResult<AssetCatalogTableQuery, any> | QueryResult<AssetCatalogGroupTableQuery, any>;
  assets: Asset[] | undefined;
  error: PythonErrorFragment | undefined;
} {
  const assetsQuery = useQuery<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>(
    ASSET_CATALOG_TABLE_QUERY,
    {
      skip: !!groupSelector,
      notifyOnNetworkStatusChange: true,
    },
  );
  const groupQuery = useQuery<AssetCatalogGroupTableQuery, AssetCatalogGroupTableQueryVariables>(
    ASSET_CATALOG_GROUP_TABLE_QUERY,
    {
      skip: !groupSelector,
      variables: {group: groupSelector},
      notifyOnNetworkStatusChange: true,
    },
  );

  return React.useMemo(() => {
    if (groupSelector) {
      const assetNodes = groupQuery.data?.assetNodes;
      return {
        query: groupQuery,
        error: undefined,
        assets: assetNodes?.map(definitionToAssetTableFragment),
      };
    }

    const assetsOrError = assetsQuery.data?.assetsOrError;
    return {
      query: assetsQuery,
      error: assetsOrError?.__typename === 'PythonError' ? assetsOrError : undefined,
      assets: assetsOrError?.__typename === 'AssetConnection' ? assetsOrError.nodes : undefined,
    };
  }, [assetsQuery, groupQuery, groupSelector]);
}

interface AssetCatalogTableProps {
  prefixPath: string[];
  setPrefixPath: (prefixPath: string[]) => void;
  groupSelector?: AssetGroupSelector;
  trace?: ReturnType<typeof useStartTrace>;
}

export const AssetsCatalogTable = ({
  prefixPath,
  setPrefixPath,
  groupSelector,
  trace,
}: AssetCatalogTableProps) => {
  const [view, setView] = useAssetView();
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});
  const [searchGroups, setSearchGroups] = useQueryPersistedState<AssetGroupSelector[]>({
    queryKey: 'g',
    decode: (qs) => (qs.groups ? JSON.parse(qs.groups) : []),
    encode: (groups) => ({groups: groups.length ? JSON.stringify(groups) : undefined}),
  });

  const searchPath = (search || '')
    .replace(/(( ?> ?)|\.|\/)/g, '/')
    .toLowerCase()
    .trim();

  const {assets, query, error} = useAllAssets(groupSelector);
  const assetGroupOptions = useAssetGroupSelectorsForAssets(assets);
  const pathMatches = useAssetSearch(searchPath, assets || []);

  const filtered = React.useMemo(
    () =>
      pathMatches.filter(
        (a) =>
          !searchGroups.length || searchGroups.some((g) => isEqual(buildAssetGroupSelector(a), g)),
      ),
    [pathMatches, searchGroups],
  );

  const {displayPathForAsset, displayed} =
    view === 'flat'
      ? buildFlatProps(filtered, prefixPath)
      : buildNamespaceProps(filtered, prefixPath);

  const refreshState = useQueryRefreshAtInterval(query, FIFTEEN_SECONDS);

  const loaded = !!assets;
  React.useEffect(() => {
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
          <TextInput
            value={search || ''}
            style={{width: '30vw', minWidth: 150, maxWidth: 400}}
            placeholder={
              prefixPath.length
                ? `Filter asset keys in ${prefixPath.join('/')}…`
                : `Filter asset keys…`
            }
            onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
          />
          {!groupSelector ? (
            <AssetGroupSuggest
              assetGroups={assetGroupOptions}
              value={searchGroups}
              onChange={setSearchGroups}
            />
          ) : undefined}
        </>
      }
      refreshState={refreshState}
      prefixPath={prefixPath || []}
      searchPath={searchPath}
      searchGroups={searchGroups}
      displayPathForAsset={displayPathForAsset}
      requery={(_) => [{query: ASSET_CATALOG_TABLE_QUERY}]}
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
