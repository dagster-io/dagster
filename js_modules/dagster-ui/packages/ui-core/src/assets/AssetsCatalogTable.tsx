import {gql, useApolloClient} from '@apollo/client';
import {Box, ButtonGroup, TextInput} from '@dagster-io/ui-components';
import isEqual from 'lodash/isEqual';
import * as React from 'react';

import {buildAssetGroupSelector, useAssetGroupSelectorsForAssets} from './AssetGroupSuggest';
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
import {useAssetSearch} from './useAssetSearch';
import {AssetViewType, useAssetView} from './useAssetView';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {AssetGroupSelector, ChangeReason} from '../graphql/types';
import {useConstantCallback} from '../hooks/useConstantCallback';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {PageLoadTrace} from '../performance';
import {useFilters} from '../ui/Filters';
import {useAssetGroupFilter} from '../ui/Filters/useAssetGroupFilter';
import {useAssetOwnerFilter, useAssetOwnersForAssets} from '../ui/Filters/useAssetOwnerFilter';
import {useChangedFilter} from '../ui/Filters/useChangedFilter';
import {
  useAssetKindTagsForAssets,
  useComputeKindTagFilter,
} from '../ui/Filters/useComputeKindTagFilter';
import {FilterObject} from '../ui/Filters/useFilter';
import {LoadingSpinner} from '../ui/Loading';
type Asset = AssetTableFragment;

let globalTableCache: AssetCatalogTableQuery;
const groupTableCache = new Map();

function useAllAssets(groupSelector?: AssetGroupSelector) {
  const client = useApolloClient();
  const [{error, assets}, setErrorAndAssets] = React.useState<{
    error: PythonErrorFragment | undefined;
    assets: Asset[] | undefined;
  }>({error: undefined, assets: undefined});

  const assetsQuery = useConstantCallback(async () => {
    function onData(queryData: typeof data) {
      const assetsOrError = queryData?.assetsOrError;
      setErrorAndAssets({
        error: assetsOrError?.__typename === 'PythonError' ? assetsOrError : undefined,
        assets: assetsOrError?.__typename === 'AssetConnection' ? assetsOrError.nodes : undefined,
      });
    }
    if (globalTableCache) {
      onData(globalTableCache);
    }
    const {data} = await client.query<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>({
      query: ASSET_CATALOG_TABLE_QUERY,
      fetchPolicy: 'no-cache',
    });
    globalTableCache = data;
    onData(data);
  });

  const groupQuery = React.useCallback(async () => {
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

  return React.useMemo(() => {
    return {
      assets,
      error,
      query: groupSelector ? groupQuery : assetsQuery,
    };
  }, [assets, assetsQuery, error, groupQuery, groupSelector]);
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
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});

  const [filters, setFilters] = useQueryPersistedState<{
    groups: AssetGroupSelector[];
    computeKindTags: string[];
    changedInBranch: ChangeReason[];
    owners: string[];
  }>({
    encode: ({groups, computeKindTags, changedInBranch, owners}) => ({
      groups: groups?.length ? JSON.stringify(groups) : undefined,
      computeKindTags: computeKindTags?.length ? JSON.stringify(computeKindTags) : undefined,
      changedInBranch: changedInBranch?.length ? JSON.stringify(changedInBranch) : undefined,
      owners: owners?.length ? JSON.stringify(owners) : undefined,
    }),
    decode: (qs) => ({
      groups: qs.groups ? JSON.parse(qs.groups) : [],
      computeKindTags: qs.computeKindTags ? JSON.parse(qs.computeKindTags) : [],
      changedInBranch: qs.changedInBranch ? JSON.parse(qs.changedInBranch) : [],
      owners: qs.owners ? JSON.parse(qs.owners) : [],
    }),
  });

  const searchPath = (search || '')
    .replace(/(( ?> ?)|\.|\/)/g, '/')
    .toLowerCase()
    .trim();

  const {assets, query, error} = useAllAssets(groupSelector);
  const pathMatches = useAssetSearch(searchPath, assets || []);

  const filtered = React.useMemo(
    () =>
      pathMatches.filter((a) => {
        if (filters.groups?.length) {
          if (!filters.groups.some((g) => isEqual(buildAssetGroupSelector(a), g))) {
            return false;
          }
        }

        if (filters.computeKindTags?.length) {
          if (!filters.computeKindTags.includes(a.definition?.computeKind ?? '')) {
            return false;
          }
        }

        if (filters.changedInBranch?.length) {
          if (
            !a.definition?.changedReasons.find((reason) =>
              filters.changedInBranch!.includes(reason),
            )
          ) {
            return false;
          }
        }

        if (filters.owners?.length) {
          const owners =
            a.definition?.owners.map((o) =>
              o.__typename === 'TeamAssetOwner' ? o.team : o.email,
            ) || [];
          if (filters.owners.some((owner) => !owners.includes(owner))) {
            return false;
          }
        }
        return true;
      }),
    [filters, pathMatches],
  );

  const {displayPathForAsset, displayed} =
    view === 'flat'
      ? buildFlatProps(filtered, prefixPath)
      : buildNamespaceProps(filtered, prefixPath);

  const refreshState = useRefreshAtInterval({
    refresh: query,
    intervalMs: FIFTEEN_SECONDS,
    leading: true,
  });

  const loaded = !!assets;
  React.useEffect(() => {
    if (loaded) {
      trace?.endTrace();
    }
  }, [loaded, trace]);

  const setVisibleAssetGroups = React.useCallback(
    (groups: AssetGroupSelector[]) => {
      setFilters((existingFilters: typeof filters) => ({
        ...existingFilters,
        groups,
      }));
    },
    [setFilters],
  );

  const setVisibleComputeKindTags = React.useCallback(
    (computeKindTags: string[]) => {
      setFilters((existingFilters: typeof filters) => ({
        ...existingFilters,
        computeKindTags,
      }));
    },
    [setFilters],
  );

  const setOwners = React.useCallback(
    (owners: string[]) => {
      setFilters((existingFilters: typeof filters) => ({
        ...existingFilters,
        owners,
      }));
    },
    [setFilters],
  );

  const setVisibleChangedInBranch = React.useCallback(
    (changeReasons: ChangeReason[]) => {
      setFilters((existingFilters: typeof filters) => ({
        ...existingFilters,
        changedInBranch: changeReasons,
      }));
    },
    [setFilters],
  );

  const allAssetGroupOptions = useAssetGroupSelectorsForAssets(pathMatches);
  const allComputeKindTags = useAssetKindTagsForAssets(pathMatches);
  const allAssetOwners = useAssetOwnersForAssets(pathMatches);

  const groupsFilter = useAssetGroupFilter({
    assetGroups: allAssetGroupOptions,
    visibleAssetGroups: filters.groups,
    setGroupFilters: setVisibleAssetGroups,
  });
  const changedInBranchFilter = useChangedFilter({
    changedInBranch: filters.changedInBranch,
    setChangedInBranch: setVisibleChangedInBranch,
  });
  const computeKindFilter = useComputeKindTagFilter({
    allComputeKindTags,
    computeKindTags: filters.computeKindTags,
    setComputeKindTags: setVisibleComputeKindTags,
  });
  const ownersFilter = useAssetOwnerFilter({
    allAssetOwners,
    owners: filters.owners,
    setOwners,
  });
  const uiFilters: FilterObject[] = [groupsFilter, computeKindFilter, ownersFilter];
  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  if (isBranchDeployment) {
    uiFilters.push(changedInBranchFilter);
  }
  const {button, activeFiltersJsx} = useFilters({filters: uiFilters});

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
      isFiltered={
        !!(
          filters.changedInBranch?.length ||
          filters.computeKindTags?.length ||
          filters.groups?.length ||
          filters.owners?.length
        )
      }
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
          {button}
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
        </>
      }
      belowActionBarComponents={
        activeFiltersJsx.length ? (
          <Box
            border="top-and-bottom"
            padding={12}
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
