import {useContext, useLayoutEffect, useMemo, useState} from 'react';

import {ApolloClient, ApolloQueryResult, gql, useApolloClient} from '../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorFragment} from '../app/types/PythonErrorFragment.types';
import {tokenForAssetKey} from '../asset-graph/Utils';
import {AssetGroupSelector, AssetKey} from '../graphql/types';
import {CacheData} from '../search/useIndexedDBCachedQuery';
import {hashObject} from '../util/hashObject';
import {cache} from '../util/idb-lru-cache';
import {weakMapMemoize} from '../util/weakMapMemoize';
import {
  AssetRecordsQuery,
  AssetRecordsQueryVariables,
  AssetRecordsQueryVersion,
} from './types/useAllAssets.types';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';
import {
  LocationWorkspaceAssetsQuery,
  WorkspaceAssetFragment,
} from '../workspace/WorkspaceContext/types/WorkspaceQueries.types';

export type AssetRecord = Extract<
  AssetRecordsQuery['assetRecordsOrError'],
  {__typename: 'AssetRecordConnection'}
>['assets'][0];

const POLL_INTERVAL = 60000 * 5; // 5 minutes
const RETRY_INTERVAL = 1000; // 1 second

const DEFAULT_BATCH_LIMIT = 1000;

export function useAllAssetsNodes() {
  const {assetEntries, loadingAssets: loading} = useContext(WorkspaceContext);
  const allAssetNodes = useMemo(() => getAllAssetNodes(assetEntries), [assetEntries]);
  return {assets: allAssetNodes, loading};
}

export function useAllAssets({
  groupSelector,
  batchLimit = DEFAULT_BATCH_LIMIT,
}: {
  groupSelector?: AssetGroupSelector;
  batchLimit?: number;
} = {}) {
  const client = useApolloClient();
  const manager = getFetchManager(client);
  const [materializedAssets, setMaterializedAssets] = useState<AssetRecord[]>(() => {
    const assetsOrError = manager.getAssetsOrError();
    if (assetsOrError instanceof Array) {
      return assetsOrError;
    }
    return [];
  });

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

  const {assets: allAssetNodes, loading: allAssetNodesLoading} = useAllAssetsNodes();

  const allAssetNodesByKey = useMemo(() => getAllAssetNodesByKey(allAssetNodes), [allAssetNodes]);

  const assets = useMemo(
    () =>
      combineSDAsAndExternalAssetsAndFilterByGroup(
        allAssetNodesByKey,
        materializedAssets,
        allAssetNodes,
        groupSelector,
      ),
    [allAssetNodesByKey, materializedAssets, allAssetNodes, groupSelector],
  );

  const assetsByAssetKey = useMemo(() => getAssetsByAssetKey(assets), [assets]);

  return {
    assets,
    loading: loading || allAssetNodesLoading,
    query: manager.fetchAssets,
    assetsByAssetKey,
    error,
  };
}

export type Asset = ReturnType<typeof useAllAssets>['assets'][number];

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
    } else {
      this._cache.delete('data');
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

  public fetchAssets = async (pollInterval = POLL_INTERVAL) => {
    if (this._fetchPromise) {
      return this._fetchPromise;
    }
    if (!this._subscribers.size) {
      return;
    }
    let nextAssetsOrError: AssetRecord[] | PythonErrorFragment | null = null;
    let didChange = true;
    try {
      this._fetchPromise = fetchAssets(this.client, this._batchLimit);
      nextAssetsOrError = await this._fetchPromise;
      if (hashObject(nextAssetsOrError) === hashObject(this._assetsOrError)) {
        didChange = false;
      }
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

    if (didChange) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      this._subscribers.forEach((callback) => callback(this._assetsOrError!));
    }
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

  getAssetsOrError() {
    return this._assetsOrError;
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

const getAllAssetNodes = weakMapMemoize(
  (assetEntries: Record<string, LocationWorkspaceAssetsQuery>) => {
    const allAssets = Object.values(assetEntries).flatMap((repo) => {
      if (
        repo.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry' &&
        repo.workspaceLocationEntryOrError.locationOrLoadError?.__typename === 'RepositoryLocation'
      ) {
        return repo.workspaceLocationEntryOrError.locationOrLoadError.repositories.flatMap(
          (repo) => repo.assetNodes,
        );
      }
      return [];
    });
    return getAssets(allAssets);
  },
);

const getAllAssetNodesByKey = weakMapMemoize(
  (allAssetNodes: ReturnType<typeof getAllAssetNodes>) => {
    return allAssetNodes.reduce(
      (acc, assetNode) => {
        acc[tokenForAssetKey(assetNode.key)] = true;
        return acc;
      },
      {} as Record<string, boolean>,
    );
  },
);

const getAssets = weakMapMemoize((allAssetNodes: WorkspaceAssetFragment[]) => {
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

  const softwareDefinedAssets: {
    __typename: 'Asset';
    key: AssetKey;
    definition: WorkspaceAssetFragment;
    id: string;
  }[] = [];

  const addedKeys = new Set();

  softwareDefinedAssetsWithDuplicates.forEach((asset) => {
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
    const duplicate = addedKeys.has(key);
    addedKeys.add(key);
    if (duplicate) {
      return;
    }
    if (!keysWithMultipleDefinitions.has(key)) {
      softwareDefinedAssets.push(asset);
      return;
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

    softwareDefinedAssets.push(
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      combineAssetDefinitions(assetToReturn!, softwareDefinedAssetsByAssetKey[key]!),
    );
  });

  return softwareDefinedAssets;
});

const filteredSDAs = weakMapMemoize(
  (sdaAssets: ReturnType<typeof getAssets>, groupSelector?: AssetGroupSelector) => {
    if (!groupSelector) {
      return sdaAssets;
    }
    return sdaAssets.filter(
      (asset) =>
        asset.definition?.groupName === groupSelector.groupName &&
        asset.definition?.repository.name === groupSelector.repositoryName &&
        asset.definition?.repository.location.name === groupSelector.repositoryLocationName,
    );
  },
);

const combineSDAsAndExternalAssetsAndFilterByGroup = weakMapMemoize(
  (
    allAssetNodesByKey: Record<string, boolean>,
    materializedAssets: AssetRecord[],
    sdaAssets: ReturnType<typeof getAssets>,
    groupSelector?: AssetGroupSelector,
  ) => {
    const externalAssets = materializedAssets
      .filter((asset) => !allAssetNodesByKey[tokenForAssetKey(asset.key)])
      .map((externalAsset) => ({
        __typename: 'Asset' as const,
        id: externalAsset.id,
        key: externalAsset.key,
        definition: null,
      }));

    return [...filteredSDAs(sdaAssets, groupSelector), ...externalAssets];
  },
);

const getAssetsByAssetKey = weakMapMemoize(
  (assets: ReturnType<typeof combineSDAsAndExternalAssetsAndFilterByGroup>) => {
    return new Map(assets.map((asset) => [tokenForAssetKey(asset.key), asset]));
  },
);

// The set of fields that should be merged by unioning the values from all SDA definitions across all code locations.
// Keep this in sync with the python code that merges the SDA definitions: https://github.com/dagster-io/dagster/blob/22e79ea7024bd13b197e3a2f66401197badceb75/python_modules/dagster/dagster/_core/definitions/remote_asset_graph.py#L239
const MERGE_ARRAY_KEYS = [
  'jobNames',
  'kinds',
  'opNames',
  'pools',
  'owners',
  'tags',
  'dependencyKeys',
  'dependedByKeys',
] as const;

// The set of fields that should be merged by taking the union of the values from all SDA definitions across all code locations.
// Keep this in sync with the python code that merges the SDA definitions: https://github.com/dagster-io/dagster/blob/22e79ea7024bd13b197e3a2f66401197badceb75/python_modules/dagster/dagster/_core/definitions/remote_asset_graph.py#L239
const MERGE_BOOLEAN_KEYS = [
  'isPartitioned',
  'isExecutable',
  'isObservable',
  'isMaterializable',
] as const;

const combineAssetDefinitions = weakMapMemoize(
  (
    asset: ReturnType<typeof getAssets>[number],
    sdas: ReturnType<typeof getAssets>,
  ): ReturnType<typeof getAssets>[number] => {
    return {
      ...asset,
      definition: {
        ...asset.definition,
        ...MERGE_ARRAY_KEYS.reduce(
          (acc, key) => {
            acc[key] = Array.from(new Set(sdas.map((sda) => sda.definition[key]).flat())) as any[];
            return acc;
          },
          {} as Record<string, string[]>,
        ),
        ...MERGE_BOOLEAN_KEYS.reduce(
          (acc, key) => {
            acc[key] = sdas.some((sda) => sda.definition[key]);
            return acc;
          },
          {} as Record<string, boolean>,
        ),
      },
    };
  },
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
