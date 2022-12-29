import {QueryResult, useQuery} from '@apollo/client';
import {Box, TextInput, Suggest, MenuItem, Icon, ButtonGroup} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {graphql} from '../graphql';
import {
  AssetCatalogGroupTableNodeFragment,
  AssetCatalogGroupTableQueryQuery,
  AssetCatalogTableQueryQuery,
  AssetGroupSelector,
  AssetTableFragmentFragment,
} from '../graphql/graphql';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {ClearButton} from '../ui/ClearButton';
import {LoadingSpinner} from '../ui/Loading';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

import {AssetTable} from './AssetTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {AssetTableFragment} from './types/AssetTableFragment';
import {useAssetSearch} from './useAssetSearch';
import {AssetViewType, useAssetView} from './useAssetView';

type Asset = AssetTableFragmentFragment;

function useAllAssets(
  groupSelector?: AssetGroupSelector,
): {
  query:
    | QueryResult<AssetCatalogTableQueryQuery, any>
    | QueryResult<AssetCatalogGroupTableQueryQuery, any>;
  assets: AssetTableFragment[] | undefined;
  error: PythonErrorFragment | undefined;
} {
  const assetsQuery = useQuery(ASSET_CATALOG_TABLE_QUERY, {
    skip: !!groupSelector,
    notifyOnNetworkStatusChange: true,
  });
  const groupQuery = useQuery(ASSET_CATALOG_GROUP_TABLE_QUERY, {
    skip: !groupSelector,
    variables: {group: groupSelector},
    notifyOnNetworkStatusChange: true,
  });

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
}

export const AssetsCatalogTable: React.FC<AssetCatalogTableProps> = ({
  prefixPath,
  setPrefixPath,
  groupSelector,
}) => {
  const [view, setView] = useAssetView();
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});
  const [searchGroup, setSearchGroup] = useQueryPersistedState<AssetGroupSelector | null>({
    queryKey: 'g',
    decode: (qs) => (qs.group ? JSON.parse(qs.group) : null),
    encode: (group) => ({group: group ? JSON.stringify(group) : undefined}),
  });

  const searchPath = (search || '')
    .replace(/(( ?> ?)|\.|\/)/g, '/')
    .toLowerCase()
    .trim();

  const {assets, query, error} = useAllAssets(groupSelector);
  const pathMatches = useAssetSearch(searchPath, assets || []);

  const filtered = React.useMemo(
    () =>
      pathMatches.filter((a) => !searchGroup || isEqual(buildAssetGroupSelector(a), searchGroup)),
    [pathMatches, searchGroup],
  );

  const {displayPathForAsset, displayed} =
    view === 'flat'
      ? buildFlatProps(filtered, prefixPath)
      : buildNamespaceProps(filtered, prefixPath);

  const refreshState = useQueryRefreshAtInterval(query, FIFTEEN_SECONDS);

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
            <AssetGroupSuggest assets={assets} value={searchGroup} onChange={setSearchGroup} />
          ) : undefined}
        </>
      }
      refreshState={refreshState}
      prefixPath={prefixPath || []}
      searchPath={searchPath}
      searchGroup={searchGroup}
      displayPathForAsset={displayPathForAsset}
      requery={(_) => [{query: ASSET_CATALOG_TABLE_QUERY}]}
    />
  );
};

const AssetGroupSuggest: React.FC<{
  assets: Asset[];
  value: AssetGroupSelector | null;
  onChange: (g: AssetGroupSelector | null) => void;
}> = ({assets, value, onChange}) => {
  const assetGroups = React.useMemo(
    () =>
      uniqBy(
        (assets || []).map(buildAssetGroupSelector).filter((a) => !!a) as AssetGroupSelector[],
        (a) => JSON.stringify(a),
      ).sort((a, b) => a.groupName.localeCompare(b.groupName)),
    [assets],
  );

  const repoContextNeeded = React.useMemo(() => {
    // This is a bit tricky - the first time we find a groupName it sets the key to `false`.
    // The second time, it sets the value to `true` + tells use we need to show the repo name
    const result: {[groupName: string]: boolean} = {};
    assetGroups.forEach(
      (group) => (result[group.groupName] = result.hasOwnProperty(group.groupName)),
    );
    return result;
  }, [assetGroups]);

  return (
    <Suggest<AssetGroupSelector>
      selectedItem={value}
      items={assetGroups}
      inputProps={{
        style: {width: 220},
        placeholder: 'Filter asset groups…',
        rightElement: value ? (
          <ClearButton onClick={() => onChange(null)} style={{marginTop: 5, marginRight: 4}}>
            <Icon name="cancel" />
          </ClearButton>
        ) : undefined,
      }}
      inputValueRenderer={(partition) => partition.groupName}
      itemPredicate={(query, partition) =>
        query.length === 0 || partition.groupName.includes(query)
      }
      itemsEqual={isEqual}
      itemRenderer={(assetGroup, props) => (
        <MenuItem
          active={props.modifiers.active}
          onClick={props.handleClick}
          key={JSON.stringify(assetGroup)}
          text={
            <>
              {assetGroup.groupName}
              {repoContextNeeded[assetGroup.groupName] ? (
                <span style={{opacity: 0.5, paddingLeft: 4}}>
                  {buildRepoPathForHuman(
                    assetGroup.repositoryName,
                    assetGroup.repositoryLocationName,
                  )}
                </span>
              ) : undefined}
            </>
          }
        />
      )}
      noResults={<MenuItem disabled={true} text="No asset groups" />}
      onItemSelect={onChange}
    />
  );
};

const ASSET_CATALOG_TABLE_QUERY = graphql(`
  query AssetCatalogTableQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
          id
          ...AssetTableFragment
        }
      }
      ...PythonErrorFragment
    }
  }
`);

const ASSET_CATALOG_GROUP_TABLE_QUERY = graphql(`
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
`);

// When we load the AssetCatalogTable for a particular asset group, we retrieve `assetNodes`,
// not `assets`. To narrow the scope of this difference we coerce the nodes to look like
// AssetCatalogTableQuery results.
function definitionToAssetTableFragment(
  definition: AssetCatalogGroupTableNodeFragment,
): AssetTableFragment {
  return {__typename: 'Asset', id: definition.id, key: definition.assetKey, definition};
}

function buildAssetGroupSelector(a: Asset) {
  return a.definition && a.definition.groupName
    ? {
        groupName: a.definition.groupName,
        repositoryName: a.definition.repository.name,
        repositoryLocationName: a.definition.repository.location.name,
      }
    : null;
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
