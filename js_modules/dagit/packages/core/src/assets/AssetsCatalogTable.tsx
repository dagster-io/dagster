import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Redirect, useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box, CursorPaginationControls, CursorPaginationProps, TextInput} from '../../../ui/src';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {tokenForAssetKey} from '../app/Util';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepoFilterButton} from '../instance/RepoFilterButton';
import {POLL_INTERVAL} from '../runs/useCursorPaginatedQuery';
import {Loading} from '../ui/Loading';
import {DagsterRepoOption, WorkspaceContext} from '../workspace/WorkspaceContext';
import {buildRepoPath} from '../workspace/buildRepoAddress';

import {AssetTable, ASSET_TABLE_FRAGMENT} from './AssetTable';
import {AssetViewModeSwitch} from './AssetViewModeSwitch';
import {AssetsEmptyState} from './AssetsEmptyState';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes,
} from './types/AssetCatalogTableQuery';
import {useAssetView} from './useAssetView';

const PAGE_SIZE = 50;

type Asset = AssetCatalogTableQuery_assetsOrError_AssetConnection_nodes;

export const AssetsCatalogTable: React.FC<{prefixPath?: string[]}> = ({prefixPath = []}) => {
  const {visibleRepos, allRepos} = React.useContext(WorkspaceContext);
  const [cursor, setCursor] = useQueryPersistedState<string | undefined>({queryKey: 'cursor'});
  const [search, setSearch] = useQueryPersistedState<string | undefined>({queryKey: 'q'});
  const [view, _setView] = useAssetView();
  const history = useHistory();

  useDocumentTitle(
    prefixPath && prefixPath.length ? `Assets: ${prefixPath.join(' \u203A ')}` : 'Assets',
  );

  const setView = (view: 'flat' | 'graph' | 'directory') => {
    _setView(view);
    if (view === 'flat' && prefixPath) {
      history.push('/instance/assets');
    } else if (cursor) {
      setCursor(undefined);
    }
  };

  const assetsQuery = useQuery<AssetCatalogTableQuery>(ASSET_CATALOG_TABLE_QUERY, {
    notifyOnNetworkStatusChange: true,
    skip: view === 'graph',
  });

  if (view === 'graph') {
    return <Redirect to="/instance/asset-graph" />;
  }

  return (
    <Wrapper>
      <Loading allowStaleData queryResult={assetsQuery}>
        {({assetsOrError}) => {
          if (assetsOrError.__typename === 'PythonError') {
            return <PythonErrorInfo error={assetsOrError} />;
          }

          const assets = assetsOrError.nodes;

          if (!assets.length) {
            return (
              <Box padding={{vertical: 64}}>
                <AssetsEmptyState prefixPath={prefixPath} />
              </Box>
            );
          }
          const searchSeparatorAgnostic = (search || '')
            .replace(/(( ?> ?)|\.|\/)/g, '>')
            .toLowerCase()
            .trim();

          const filtered = (visibleRepos.length === allRepos.length
            ? assets
            : filterAssetsToRepos(assets, visibleRepos)
          ).filter(
            (a) =>
              !searchSeparatorAgnostic ||
              tokenForAssetKey(a.key).toLowerCase().startsWith(searchSeparatorAgnostic),
          );

          const {displayPathForAsset, displayed, nextCursor, prevCursor} =
            view === 'flat'
              ? buildFlatProps(filtered, prefixPath, cursor)
              : buildNamespaceProps(filtered, prefixPath, cursor);

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
            <>
              <AssetTable
                assets={displayed}
                actionBarComponents={
                  <>
                    <AssetViewModeSwitch view={view} setView={setView} />
                    <RepoFilterButton />
                    <TextInput
                      value={search}
                      style={{width: '30vw', minWidth: 150, maxWidth: 400}}
                      placeholder="Search all asset_keys..."
                      onChange={(e: React.ChangeEvent<any>) => setSearch(e.target.value)}
                    />
                    <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={assetsQuery} />
                  </>
                }
                prefixPath={prefixPath || []}
                displayPathForAsset={displayPathForAsset}
                maxDisplayCount={PAGE_SIZE}
                requery={(_) => [{query: ASSET_CATALOG_TABLE_QUERY}]}
              />
              <Box margin={{vertical: 20}}>
                <CursorPaginationControls {...paginationProps} />
              </Box>
            </>
          );
        }}
      </Loading>
    </Wrapper>
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
  ${PYTHON_ERROR_FRAGMENT}
  ${ASSET_TABLE_FRAGMENT}
`;

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

const filterAssetsToRepos = (assets: Asset[], visibleRepos: DagsterRepoOption[]) => {
  const visibleRepoHashes = visibleRepos.map((v) =>
    buildRepoPath(v.repository.name, v.repositoryLocation.name),
  );
  return assets.filter(
    (a) =>
      a.definition &&
      visibleRepoHashes.includes(
        buildRepoPath(a.definition.repository.name, a.definition.repository.location.name),
      ),
  );
};
