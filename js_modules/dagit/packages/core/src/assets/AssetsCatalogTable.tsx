import {gql, QueryResult, useQuery} from '@apollo/client';
import {
  Box,
  CursorPaginationControls,
  CursorPaginationProps,
  TextInput,
  Suggest,
  MenuItem,
  Icon,
  ButtonGroup,
} from '@dagster-io/ui';
import isEqual from 'lodash/isEqual';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';
import styled from 'styled-components/macro';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {FIFTEEN_SECONDS, useMergedRefresh, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {AssetGroupSelector} from '../types/globalTypes';
import {ClearButton} from '../ui/ClearButton';
import {LoadingSpinner} from '../ui/Loading';
import {StickyTableContainer} from '../ui/StickyTableContainer';
import {buildRepoPath} from '../workspace/buildRepoAddress';

import {AssetTable, ASSET_TABLE_DEFINITION_FRAGMENT, ASSET_TABLE_FRAGMENT} from './AssetTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {AssetKey} from './types';
import {
  AssetCatalogGroupTableQuery,
  AssetCatalogGroupTableQueryVariables,
  AssetCatalogGroupTableQuery_assetNodes,
} from './types/AssetCatalogGroupTableQuery';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes,
} from './types/AssetCatalogTableQuery';
import {AssetTableFragment} from './types/AssetTableFragment';
import {AssetViewType, useAssetView} from './useAssetView';

const PAGE_SIZE = 50;

type Asset = AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes;

function useAllAssets(
  groupSelector?: AssetGroupSelector,
): {
  query: QueryResult;
  assets: AssetTableFragment[] | undefined;
  error: PythonErrorFragment | undefined;
} {
  const assetsQuery = useQuery<AssetCatalogTableQuery>(ASSET_CATALOG_TABLE_QUERY, {
    skip: !!groupSelector,
    notifyOnNetworkStatusChange: true,
  });
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
    } else {
      const assetsOrError = assetsQuery.data?.assetsOrError;
      return {
        query: assetsQuery,
        error: assetsOrError?.__typename === 'PythonError' ? assetsOrError : undefined,
        assets: assetsOrError?.__typename === 'AssetConnection' ? assetsOrError.nodes : undefined,
      };
    }
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
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey: 'cursor'});
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
  const filtered = React.useMemo(
    () =>
      (assets || []).filter((a) => {
        const groupMatch = !searchGroup || isEqual(buildAssetGroupSelector(a), searchGroup);
        const pathMatch = !searchPath || tokenForAssetKey(a.key).toLowerCase().includes(searchPath);
        return groupMatch && pathMatch;
      }),
    [assets, searchPath, searchGroup],
  );

  const {displayPathForAsset, displayed, nextCursor, prevCursor} =
    view === 'flat'
      ? buildFlatProps(filtered, prefixPath, cursor)
      : buildNamespaceProps(filtered, prefixPath, cursor);

  const displayedKeys = React.useMemo(
    () => displayed.map<AssetKey>((a) => ({path: a.key.path})),
    [displayed],
  );
  const {liveDataByNode, liveResult} = useLiveDataForAssetKeys(displayedKeys);

  const refreshState = useMergedRefresh(
    useQueryRefreshAtInterval(query, FIFTEEN_SECONDS),
    useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS),
  );

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

  const paginationProps: CursorPaginationProps = {
    hasPrevCursor: !!prevCursor,
    hasNextCursor: !!nextCursor,
    popCursor: () => setCursor(prevCursor),
    advanceCursor: () => setCursor(nextCursor),
    reset: () => {
      setCursor(undefined);
    },
  };

  return (
    <Wrapper>
      <StickyTableContainer $top={0}>
        <AssetTable
          view={view}
          assets={displayed}
          liveDataByNode={liveDataByNode}
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
                    ? `Filter asset_keys in ${prefixPath.join('/')}…`
                    : `Filter all asset_keys…`
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
          displayPathForAsset={displayPathForAsset}
          maxDisplayCount={PAGE_SIZE}
          requery={(_) => [{query: ASSET_CATALOG_TABLE_QUERY}]}
        />
      </StickyTableContainer>
      <Box padding={{bottom: 64}}>
        <CursorPaginationControls {...paginationProps} />
      </Box>
    </Wrapper>
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
                  {buildRepoPath(assetGroup.repositoryName, assetGroup.repositoryLocationName)}
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
const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  position: relative;
  z-index: 0;
`;

const ASSET_CATALOG_TABLE_QUERY = gql`
  query AssetCatalogTableQuery {
    materializedKeysOrError {
      __typename
      ... on MaterializedKeysConnection {
        nodes {
          id
          ...AssetTableFragment
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${ASSET_TABLE_FRAGMENT}
`;

const ASSET_CATALOG_GROUP_TABLE_QUERY = gql`
  query AssetCatalogGroupTableQuery($group: AssetGroupSelector) {
    assetNodes(group: $group) {
      id
      assetKey {
        path
      }
      ...AssetTableDefinitionFragment
    }
  }
  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;

// When we load the AssetCatalogTable for a particular asset group, we retrieve `assetNodes`,
// not `assets`. To narrow the scope of this difference we coerce the nodes to look like
// AssetCatalogTableQuery results.
//
function definitionToAssetTableFragment(
  definition: AssetCatalogGroupTableQuery_assetNodes,
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

function buildFlatProps(assets: Asset[], prefixPath: string[], cursor: string | undefined) {
  const cursorValue = (asset: Asset) => JSON.stringify([...prefixPath, ...asset.key.path]);
  const cursorIndex = cursor ? assets.findIndex((ns) => cursor <= cursorValue(ns)) : 0;
  const prevPageIndex = Math.max(0, cursorIndex - PAGE_SIZE);
  const nextPageIndex = cursorIndex + PAGE_SIZE;

  return {
    displayed: assets.slice(cursorIndex, cursorIndex + PAGE_SIZE),
    displayPathForAsset: (asset: Asset) => asset.key.path,
    prevCursor: cursorIndex > 0 ? cursorValue(assets[prevPageIndex]) : undefined,
    nextCursor: nextPageIndex < assets.length ? cursorValue(assets[nextPageIndex]) : undefined,
  };
}

function buildNamespaceProps(assets: Asset[], prefixPath: string[], cursor: string | undefined) {
  const namespaceForAsset = (asset: Asset) => {
    return asset.key.path.slice(prefixPath.length, prefixPath.length + 1);
  };
  const namespaces = Array.from(
    new Set(assets.map((asset) => JSON.stringify(namespaceForAsset(asset)))),
  )
    .map((x) => JSON.parse(x))
    .sort();

  const cursorValue = (ns: string[]) => JSON.stringify([...prefixPath, ...ns]);
  const cursorIndex = cursor ? namespaces.findIndex((ns) => cursor <= cursorValue(ns)) : 0;

  if (cursorIndex === -1) {
    return {
      displayPathForAsset: namespaceForAsset,
      displayed: [],
      prevCursor: undefined,
      nextCursor: undefined,
    };
  }

  const slice = namespaces.slice(cursorIndex, cursorIndex + PAGE_SIZE);
  const prevPageIndex = Math.max(0, cursorIndex - PAGE_SIZE);
  const prevCursor = cursorIndex !== 0 ? cursorValue(namespaces[prevPageIndex]) : undefined;
  const nextPageIndex = cursorIndex + PAGE_SIZE;
  const nextCursor =
    namespaces.length > nextPageIndex ? cursorValue(namespaces[nextPageIndex]) : undefined;

  return {
    nextCursor,
    prevCursor,
    displayPathForAsset: namespaceForAsset,
    displayed: filterAssetsByNamespace(
      assets,
      slice.map((ns) => [...prefixPath, ...ns]),
    ),
  };
}

const filterAssetsByNamespace = (assets: Asset[], paths: string[][]) => {
  return assets.filter((asset) =>
    paths.some((path) => path.every((part, i) => part === asset.key.path[i])),
  );
};
