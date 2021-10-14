import {gql} from '@apollo/client';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {POLL_INTERVAL, useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {Box} from '../ui/Box';
import {CursorPaginationControls} from '../ui/CursorControls';
import {Loading} from '../ui/Loading';

import {AssetSearch} from './AssetSearch';
import {AssetTable, ASSET_TABLE_FRAGMENT} from './AssetTable';
import {AssetsEmptyState} from './AssetsEmptyState';
import {
  PaginatedAssetKeysQuery,
  PaginatedAssetKeysQueryVariables,
} from './types/PaginatedAssetKeysQuery';

const PAGE_SIZE = 25;

export const AssetKeysTable: React.FC<{
  prefixPath: string[];
  switcher: React.ReactNode;
}> = ({prefixPath, switcher}) => {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    PaginatedAssetKeysQuery,
    PaginatedAssetKeysQueryVariables
  >({
    query: PAGINATED_ASSET_KEYS_QUERY,
    pageSize: PAGE_SIZE,
    variables: {
      prefix: prefixPath,
    },
    nextCursorForResult: (data) => {
      if (data.assetsOrError.__typename !== 'AssetConnection') {
        return undefined;
      }
      const node = data.assetsOrError.nodes[PAGE_SIZE - 1];
      return node ? JSON.stringify(node.key.path) : undefined;
    },
    getResultArray: (data) => {
      if (!data || data.assetsOrError.__typename !== 'AssetConnection') {
        return [];
      }
      return data.assetsOrError.nodes;
    },
  });

  return (
    <div>
      <Loading allowStaleData queryResult={queryResult}>
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

          const showSwitcher =
            prefixPath.length || assets.some((asset) => asset.key.path.length > 1);
          const {hasNextCursor, hasPrevCursor} = paginationProps;
          return (
            <>
              <AssetTable
                assets={assets}
                actionBarComponents={
                  <>
                    {showSwitcher ? switcher : null}
                    <AssetSearch />
                    <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
                  </>
                }
                prefixPath={prefixPath}
                displayPathForAsset={(asset) => asset.key.path}
                requery={(_) => [{query: PAGINATED_ASSET_KEYS_QUERY}]}
              />
              {hasNextCursor || hasPrevCursor ? (
                <Box margin={{vertical: 20}}>
                  <CursorPaginationControls {...paginationProps} />
                </Box>
              ) : null}
            </>
          );
        }}
      </Loading>
    </div>
  );
};

const PAGINATED_ASSET_KEYS_QUERY = gql`
  query PaginatedAssetKeysQuery($prefix: [String!], $limit: Int, $cursor: String) {
    assetsOrError(prefix: $prefix, limit: $limit, cursor: $cursor) {
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
