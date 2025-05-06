import {useContext, useLayoutEffect, useMemo, useState} from 'react';

import {ApolloClient, ApolloQueryResult, gql, useApolloClient} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGroupSelector} from '../graphql/types';
import {CacheData} from '../search/useIndexedDBCachedQuery';
import {cache} from '../util/idb-lru-cache';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {
  AssetRecordsQuery,
  AssetRecordsQueryVariables,
  AssetRecordsQueryVersion,
} from './types/useAllAssets.types';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {DagsterRepoOption} from '../workspace/WorkspaceContext/util';

export type AssetRecord = Extract<
  AssetRecordsQuery['assetRecordsOrError'],
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
  const [materializedAssets, setMaterializedAssets] = useState<AssetRecord[]>([]);
  const manager = getFetchManager(client);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PythonErrorFragment | null>(null);
  useLayoutEffect(() => {
    let didCleanup = false;
    manager.setBatchLimit(batchLimit);
    const unsubscribe = manager.subscribe((assetsOrError) => {
      if (didCleanup) {
        return;
      }
      if (assetsOrError instanceof Array) {
        setMaterializedAssets(assetsOrError);
      } else {
        setError(assetsOrError);
      }
      setLoading(false);
    });
    return () => {
      didCleanup = true;
      unsubscribe();
    };
  }, [manager, batchLimit]);

  const {allRepos, loading: workspaceLoading} = useContext(WorkspaceContext);
  const allAssetNodes = useMemo(() => getAllAssetNodes(allRepos), [allRepos]);

  const allAssetNodesByKey = useMemo(() => getAllAssetNodesByKey(allAssetNodes), [allAssetNodes]);

  const assets = useMemo(
    () => getAssets(materializedAssets, allAssetNodesByKey, allAssetNodes, groupSelector),
    [materializedAssets, allAssetNodesByKey, allAssetNodes, groupSelector],
  );

  const assetsByAssetKey = useMemo(() => getAssetsByAssetKey(assets), [assets]);

  return {
    assets,
    loading: loading || workspaceLoading,
    query: manager.fetchAssets,
    assetsByAssetKey,
    error,
  };
}

const getFetchManager = weakMapMemoize((client: ApolloClient<any>) => new FetchManager(client));

class FetchManager {
  private _assetsOrError: AssetRecord[] | PythonErrorFragment | null = null;
  private _subscribers = new Set<(assetsOrError: AssetRecord[] | PythonErrorFragment) => void>();
  private _started = false;
  private _fetchTimeout: NodeJS.Timeout | null = null;
  private _fetchPromise: Promise<AssetRecord[] | PythonErrorFragment> | null = null;
  private _batchLimit = DEFAULT_BATCH_LIMIT;
  private _cache: ReturnType<typeof cache<CacheData<AssetRecord[]>>>;

  constructor(private readonly client: ApolloClient<any>) {
    this._cache = cache<CacheData<AssetRecord[]>>({dbName: 'MaterializedAssets', maxCount: 1});
    this.loadFromIndexedDB(); // Load from IndexedDB on construction, intentionally not awaited.
  }

  subscribe(callback: (assetsOrError: AssetRecord[] | PythonErrorFragment) => void) {
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
    if (data && !this._assetsOrError && version === AssetRecordsQueryVersion) {
      this._assetsOrError = data;
      this._subscribers.forEach((callback) => callback(data));
    }
  }

  private saveToIndexedDB(data: AssetRecord[]) {
    this._cache.set('data', {data, version: AssetRecordsQueryVersion});
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
    let nextAssetsOrError: AssetRecord[] | PythonErrorFragment | null = null;
    try {
      this._fetchPromise = fetchAssets(this.client, this._batchLimit);
      nextAssetsOrError = await this._fetchPromise;
      this._assetsOrError = nextAssetsOrError;
    } finally {
      this._fetchPromise = null;
    }

    let nextPollInterval = POLL_INTERVAL;
    if (nextAssetsOrError instanceof Array) {
      setTimeout(() => {
        this.saveToIndexedDB(nextAssetsOrError);
      }, 32);
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
      if (this._fetchTimeout) {
        return;
      }
      this._fetchTimeout = setTimeout(() => {
        this._fetchTimeout = null;
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
  const assets: AssetRecord[] = [];
  while (hasMore) {
    const result: ApolloQueryResult<AssetRecordsQuery> = await client.query<
      AssetRecordsQuery,
      AssetRecordsQueryVariables
    >({
      query: ASSET_RECORDS_QUERY,
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

const getAllAssetNodes = weakMapMemoize((allRepos: DagsterRepoOption[]) => {
  return allRepos.flatMap((repo) => repo.repository.assetNodes);
});

const getAllAssetNodesByKey = weakMapMemoize(
  (allAssetNodes: AssetTableDefinitionFragment[]) => {
    return allAssetNodes.reduce(
      (acc, assetNode) => {
        acc[tokenForAssetKey(assetNode.assetKey)] = true;
        return acc;
      },
      {} as Record<string, boolean>,
    );
  },
  {ttl: POLL_INTERVAL, maxEntries: 2},
);

const getAssets = weakMapMemoize(
  (
    materializedAssets: AssetRecord[],
    allAssetNodesByKey: Record<string, boolean>,
    allAssetNodes: AssetTableDefinitionFragment[],
    groupSelector?: AssetGroupSelector,
  ) => {
    const softwareDefinedAssetsWithDuplicates = allAssetNodes.map((assetNode) => ({
      __typename: 'Asset' as const,
      id: assetNode.id,
      key: assetNode.assetKey,
      definition: assetNode,
    }));

    const softwareDefinedAssetsByAssetKey: Record<
      string,
      (typeof softwareDefinedAssetsWithDuplicates)[number][]
    > = {};
    const keysWithMultipleDefinitions: Set<string> = new Set();
    for (const asset of softwareDefinedAssetsWithDuplicates) {
      const key = tokenForAssetKey(asset.key);
      softwareDefinedAssetsByAssetKey[key] = softwareDefinedAssetsByAssetKey[key] || [];
      softwareDefinedAssetsByAssetKey[key].push(asset);
      if (softwareDefinedAssetsByAssetKey[key].length > 1) {
        keysWithMultipleDefinitions.add(key);
      }
    }

    const softwareDefinedAssets = softwareDefinedAssetsWithDuplicates.filter((asset) => {
      /**
       * Return a materialization node if it exists, otherwise return an observable node if it
       * exists, otherwise return any non-stub node, otherwise return any node.
       * This exists to preserve implicit behavior, where the
       * materialization node was previously preferred over the observable node. This is a
       * temporary measure until we can appropriately scope the accessors that could apply to
       * either a materialization or observation node.
       * This property supports existing behavior but it should be phased out, because it relies on
       * materialization nodes shadowing observation nodes that would otherwise be exposed.
       */
      const key = tokenForAssetKey(asset.key);
      if (!keysWithMultipleDefinitions.has(key)) {
        return true;
      }
      const materializableAsset = softwareDefinedAssetsByAssetKey[key]?.find(
        (a) => a.definition?.isMaterializable,
      );
      const observableAsset = softwareDefinedAssetsByAssetKey[key]?.find(
        (a) => a.definition?.isObservable,
      );
      const nonGeneratedAsset = softwareDefinedAssetsByAssetKey[key]?.find(
        (a) => !a.definition?.isAutoCreatedStub && a.definition,
      );
      const assetWithRepo = softwareDefinedAssetsByAssetKey[key]?.find((a) => !!a.definition);
      const anyAsset = softwareDefinedAssetsByAssetKey[key]?.[0];

      const assetToReturn =
        materializableAsset || observableAsset || nonGeneratedAsset || assetWithRepo || anyAsset;

      return assetToReturn === asset;
    });

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
  },
);

const getAssetsByAssetKey = weakMapMemoize(
  (assets: ReturnType<typeof getAssets>) => {
    return new Map(assets.map((asset) => [tokenForAssetKey(asset.key), asset]));
  },
  {ttl: POLL_INTERVAL, maxEntries: 2},
);

export const ASSET_RECORDS_QUERY = gql`
  query AssetRecordsQuery($cursor: String, $limit: Int) {
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
