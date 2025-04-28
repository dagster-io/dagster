import {useContext, useLayoutEffect, useMemo, useState} from 'react';

import {ApolloClient, ApolloQueryResult, gql, useApolloClient} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGroupSelector} from '../graphql/types';
import {CacheData} from '../search/useIndexedDBCachedQuery';
import {cache} from '../util/idb-lru-cache';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {AssetsStateQuery, AssetsStateQueryVariables} from './types/useAllAssets.types';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

export type AssetState = Extract<
  AssetsStateQuery['assetRecordsOrError'],
  {__typename: 'AssetRecordConnection'}
>['assets'][0];

const POLL_INTERVAL = 60000; // 1 minute
const RETRY_INTERVAL = 1000; // 1 second

const DEFAULT_BATCH_LIMIT = 10000;

export function useAllAssets({
  groupSelector,
  batchLimit = DEFAULT_BATCH_LIMIT,
}: {
  groupSelector?: AssetGroupSelector;
  batchLimit?: number;
} = {}) {
  const client = useApolloClient();
  const [materializedAssets, setMaterializedAssets] = useState<AssetState[]>([]);
  const manager = getFetchManager(client);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PythonErrorFragment | null>(null);
  useLayoutEffect(() => {
    manager.setBatchLimit(batchLimit);
    return manager.subscribe((assetsOrError) => {
      if (assetsOrError instanceof Array) {
        setMaterializedAssets(assetsOrError);
      } else {
        setError(assetsOrError);
      }
      setLoading(false);
    });
  }, [manager, batchLimit]);

  const {allRepos, loading: workspaceLoading} = useContext(WorkspaceContext);
  const allAssetNodes = useMemo(() => {
    return allRepos.flatMap((repo) => repo.repository.assetNodes);
  }, [allRepos]);

  const allAssetNodesByKey = useMemo(() => {
    return allAssetNodes.reduce(
      (acc, assetNode) => {
        acc[tokenForAssetKey(assetNode.assetKey)] = true;
        return acc;
      },
      {} as Record<string, boolean>,
    );
  }, [allAssetNodes]);

  const assets = useMemo(() => {
    const softwareDefinedAssets = allAssetNodes.map((assetNode) => ({
      __typename: 'Asset' as const,
      id: assetNode.id,
      key: assetNode.assetKey,
      definition: assetNode,
    }));

    if (groupSelector) {
      return softwareDefinedAssets.filter(
        (asset) =>
          asset.definition.groupName === groupSelector.groupName &&
          asset.definition.repository.name === groupSelector.repositoryName &&
          asset.definition.repository.location.name === groupSelector.repositoryLocationName,
      );
    }

    // Assets returned by the assetRecordsOrError resolver but not returned by the WorkspaceContext
    // don't have a definition and are "external assets"
    const externalAssets = materializedAssets
      .filter((asset) => !allAssetNodesByKey[tokenForAssetKey(asset.key)])
      .map((externalAsset) => ({
        __typename: 'Asset' as const,
        id: externalAsset.id,
        key: externalAsset.key,
        definition: null,
      }));

    return [...externalAssets, ...softwareDefinedAssets];
  }, [materializedAssets, allAssetNodesByKey, allAssetNodes, groupSelector]);

  const assetsByAssetKey = useMemo(() => {
    return new Map(assets.map((asset) => [tokenForAssetKey(asset.key), asset]));
  }, [assets]);

  return {
    assets,
    loading: loading || workspaceLoading,
    query: manager.fetchAssets,
    assetsByAssetKey,
    error,
  };
}

const getFetchManager = weakMapMemoize((client: ApolloClient<any>) => new FetchManager(client));

const VERSION = 1;
class FetchManager {
  private _assetsOrError: AssetState[] | PythonErrorFragment | null = null;
  private _subscribers = new Set<(assetsOrError: AssetState[] | PythonErrorFragment) => void>();
  private _started = false;
  private _fetchTimeout: NodeJS.Timeout | null = null;
  private _fetchPromise: Promise<AssetState[] | PythonErrorFragment> | null = null;
  private _batchLimit = DEFAULT_BATCH_LIMIT;
  private _cache: ReturnType<typeof cache<CacheData<AssetState[]>>>;

  constructor(private readonly client: ApolloClient<any>) {
    this._cache = cache<CacheData<AssetState[]>>({dbName: 'MaterializedAssets', maxCount: 1});
    this.loadFromIndexedDB();
  }

  subscribe(callback: (assetsOrError: AssetState[] | PythonErrorFragment) => void) {
    this._subscribers.add(callback);
    this.startFetchLoop();

    if (this._assetsOrError) {
      callback(this._assetsOrError);
    }

    return () => {
      this._subscribers.delete(callback);
      if (!this._subscribers.size) {
        this.stopFetchLoop();
      }
    };
  }

  private async loadFromIndexedDB() {
    const result = await this._cache.get('data');
    if (!result) {
      return;
    }
    const {data, version} = result.value;
    if (data && !this._assetsOrError && version === VERSION) {
      this._assetsOrError = data;
      this._subscribers.forEach((callback) => callback(data));
    }
  }

  private saveToIndexedDB(data: AssetState[]) {
    this._cache.set('data', {data, version: VERSION});
  }

  private startFetchLoop() {
    if (this._started) {
      return;
    }
    this._started = true;
    this.fetchAssets();
  }

  private stopFetchLoop() {
    this._started = false;
    if (this._fetchTimeout) {
      clearTimeout(this._fetchTimeout);
      this._fetchTimeout = null;
    }
  }

  public fetchAssets = async (pollInterval = POLL_INTERVAL) => {
    if (this._fetchPromise) {
      return this._fetchPromise;
    }
    this._fetchPromise = fetchAssets(this.client, this._batchLimit);
    this._assetsOrError = await this._fetchPromise;
    this._fetchPromise = null;

    let nextPollInterval = POLL_INTERVAL;
    if (this._assetsOrError instanceof Array) {
      this.saveToIndexedDB(this._assetsOrError);
    } else {
      if (pollInterval === RETRY_INTERVAL) {
        // if we're already polling at 1s then set the poll interval back to 1m
        // to avoid spamming the server with a failing request...
        nextPollInterval = POLL_INTERVAL;
      } else {
        nextPollInterval = RETRY_INTERVAL; // try again in 1 second if there was an error
      }
    }

    this._subscribers.forEach((callback) => callback(this._assetsOrError!));
    if (this._subscribers.size) {
      this._fetchTimeout = setTimeout(() => {
        this.fetchAssets();
      }, nextPollInterval);
    }
    return this._assetsOrError;
  };

  setBatchLimit(batchLimit: number) {
    this._batchLimit = batchLimit;
  }
}

async function fetchAssets(client: ApolloClient<any>, batchLimit: number) {
  let cursor = undefined;
  let hasMore = true;
  const assets: AssetState[] = [];
  while (hasMore) {
    const result: ApolloQueryResult<AssetsStateQuery> = await client.query<
      AssetsStateQuery,
      AssetsStateQueryVariables
    >({
      query: ASSETS_STATE_QUERY,
      variables: {cursor, limit: batchLimit},
    });
    if (!result || result.error) {
      throw new Error(result.error?.message ?? 'Unknown error');
    }
    if (result.data.assetRecordsOrError.__typename === 'AssetRecordConnection') {
      hasMore = result.data.assetRecordsOrError.assets.length === batchLimit;
      cursor = result.data.assetRecordsOrError.cursor;
      assets.push(...result.data.assetRecordsOrError.assets);
    }
    if (result.data.assetRecordsOrError.__typename === 'PythonError') {
      return result.data.assetRecordsOrError;
    }
  }
  return assets;
}

export const ASSETS_STATE_QUERY = gql`
  query AssetsStateQuery($cursor: String, $limit: Int) {
    assetRecordsOrError(cursor: $cursor, limit: $limit) {
      ...PythonErrorFragment
      ... on AssetRecordConnection {
        assets {
          id
          key {
            path
          }
        }
        cursor
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
