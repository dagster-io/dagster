import {useMemo} from 'react';
import {observeEnabled} from 'shared/app/observeEnabled.oss';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {tokenForAssetKey, tokenToAssetKey} from '../asset-graph/Utils';
import {useAllAssetsNodes} from '../assets/useAllAssets';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {
  AssetHealthFragment,
  AssetHealthQuery,
  AssetHealthQueryVariables,
} from './types/AssetHealthDataProvider.types';
import {weakMapMemoize} from '../util/weakMapMemoize';

const BATCH_SIZE = 250;
const PARALLEL_FETCHES = 4;

const EMPTY_ARRAY: any[] = [];

function init() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      const assetKeys = keys.map(tokenToAssetKey);

      const healthResponse = await client.query<AssetHealthQuery, AssetHealthQueryVariables>({
        query: ASSETS_HEALTH_INFO_QUERY,
        fetchPolicy: 'no-cache',
        variables: {
          assetKeys,
        },
      });

      const assetData = healthResponse.data.assetsOrError;
      if (assetData.__typename === 'PythonError') {
        showCustomAlert({
          title: 'An error occurred',
          body: <PythonErrorInfo error={assetData} />,
        });
        return {};
      } else if (assetData.__typename === 'AssetConnection') {
        const result: Record<string, AssetHealthFragment> = Object.fromEntries(
          assetData.nodes.map((node) => [tokenForAssetKey(node.key), node]),
        );
        // provide null values for any keys that do not have results returned by the query
        keys.forEach((key) => {
          if (!result[key]) {
            result[key] = {
              __typename: 'Asset',
              key: {
                __typename: 'AssetKey',
                ...tokenToAssetKey(key),
              },
              latestMaterializationTimestamp: null,
              latestFailedToMaterializeTimestamp: null,
              freshnessStatusChangedTimestamp: null,
              assetHealth: null,
            };
          }
        });
        return result;
      } else {
        showCustomAlert({
          title: 'An unknown error occurred',
        });
        return {};
      }
    },
    BATCH_SIZE,
    PARALLEL_FETCHES,
  );
}
export const AssetHealthData = init();

export function useAssetHealthData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  /**
   * Skip fetching health data for assets that don't have definitions because it is expensive.
   * Instead we'll just return an empty asset health fragment.
   */
  const {allAssetKeys} = useAllAssetsNodes();
  const shouldSkip = !allAssetKeys.has(tokenForAssetKey(assetKey));
  const result = AssetHealthData.useLiveDataSingle(tokenForAssetKey(assetKey), thread, shouldSkip);
  useBlockTraceUntilTrue('useAssetHealthData', !!result.liveData, {skip: shouldSkip});
  const liveData = useMemo(() => {
    return shouldSkip ? buildEmptyAssetHealthFragment(tokenForAssetKey(assetKey)) : result.liveData;
  }, [result.liveData, shouldSkip, assetKey]);
  return {
    ...result,
    liveData,
  };
}

const memoizedAssetKeys = weakMapMemoize((assetKeys: AssetKeyInput[]) => {
  return assetKeys.map((key) => tokenForAssetKey(key));
});

type AssetsHealthDataConfig = {
  assetKeys: AssetKeyInput[];
  thread?: LiveDataThreadID;
  blockTrace?: boolean;
  skip?: boolean;
  loading?: boolean;
};

/**
 * Categorizes asset keys based on whether they have definitions or not.
 * Keys with definitions need health data fetching, while keys without definitions
 * get empty health fragments.
 */
function categorizeAssetKeys(
  assetKeys: AssetKeyInput[],
  allAssetKeys: Set<string>,
): {keysWithDefinitions: AssetKeyInput[]; keysWithoutDefinitions: AssetKeyInput[]} {
  const keysWithDefinitions: AssetKeyInput[] = [];
  const keysWithoutDefinitions: AssetKeyInput[] = [];

  assetKeys.forEach((key) => {
    const tokenKey = tokenForAssetKey(key);
    if (allAssetKeys.has(tokenKey)) {
      keysWithDefinitions.push(key);
    } else {
      keysWithoutDefinitions.push(key);
    }
  });

  return {keysWithDefinitions, keysWithoutDefinitions};
}

/**
 * Creates empty health fragments for assets without definitions.
 * These assets don't need expensive health data fetching.
 */
function createEmptyHealthFragments(
  keysWithoutDefinitions: AssetKeyInput[],
): Record<string, AssetHealthFragment> {
  return Object.fromEntries(
    keysWithoutDefinitions.map((key) => {
      const tokenKey = tokenForAssetKey(key);
      return [tokenKey, buildEmptyAssetHealthFragment(tokenKey)];
    }),
  );
}

/**
 * Merges live data results with empty health fragments for a complete dataset.
 */
function mergeHealthData(
  liveDataResult: ReturnType<typeof AssetHealthData.useLiveData>,
  emptyFragments: Record<string, AssetHealthFragment>,
) {
  return {
    ...liveDataResult,
    liveDataByNode: {
      ...liveDataResult.liveDataByNode,
      ...emptyFragments,
    },
  };
}

/**
 * Determines if the trace should be blocked based on loading status and data completeness.
 */
function shouldBlockTrace(
  loading: boolean,
  blockTrace: boolean,
  currentDataCount: number,
  expectedDataCount: number,
): boolean {
  // Don't block if still loading
  if (loading) {
    return false;
  }

  // Don't block if blockTrace is disabled
  if (!blockTrace) {
    return false;
  }

  // Block until we have all expected data
  return currentDataCount === expectedDataCount;
}

// Get assets health data, with an `observeEnabled` check included to effectively no-op any users
// who are not gated in.
export function useAssetsHealthData({assetKeys, ...rest}: AssetsHealthDataConfig) {
  return useAssetsHealthDataWithoutGateCheck({
    ...rest,
    assetKeys: observeEnabled() ? assetKeys : EMPTY_ARRAY,
  });
}

// Get assets health data, with no `observeEnabled` check. This allows us to dark launch
// asset health checking without depending on the `observeEnabled` check.
export function useAssetsHealthDataWithoutGateCheck({
  assetKeys,
  thread = 'AssetHealth', // Use AssetHealth to get 250 batch size
  blockTrace = true,
  skip = false,
  loading = false,
}: AssetsHealthDataConfig) {
  const {allAssetKeys} = useAllAssetsNodes();

  // Step 1: Categorize keys based on whether they have definitions
  const {keysWithDefinitions, keysWithoutDefinitions} = useMemo(
    () => categorizeAssetKeys(assetKeys, allAssetKeys),
    [assetKeys, allAssetKeys],
  );

  // Step 2: Fetch live data for keys with definitions
  const liveDataResult = AssetHealthData.useLiveData(
    memoizedAssetKeys(keysWithDefinitions),
    thread,
    skip,
  );

  // Step 3: Create empty fragments for keys without definitions
  const emptyHealthFragments = useMemo(
    () => createEmptyHealthFragments(keysWithoutDefinitions),
    [keysWithoutDefinitions],
  );

  // Step 4: Merge live data with empty fragments
  const fullResult = useMemo(
    () => mergeHealthData(liveDataResult, emptyHealthFragments),
    [liveDataResult, emptyHealthFragments],
  );

  // Step 5: Block trace until data is ready
  const traceReady = shouldBlockTrace(
    loading,
    blockTrace,
    Object.keys(fullResult.liveDataByNode).length,
    assetKeys.length,
  );

  useBlockTraceUntilTrue('useAssetsHealthData', traceReady, {skip});

  return fullResult;
}

export const ASSETS_HEALTH_INFO_QUERY = gql`
  query AssetHealthQuery($assetKeys: [AssetKeyInput!]!) {
    assetsOrError(assetKeys: $assetKeys) {
      ... on AssetConnection {
        nodes {
          id
          ...AssetHealthFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  fragment AssetHealthFragment on Asset {
    key {
      path
    }

    latestMaterializationTimestamp
    latestFailedToMaterializeTimestamp
    freshnessStatusChangedTimestamp

    assetHealth {
      assetHealth
      materializationStatus
      materializationStatusMetadata {
        ...AssetHealthMaterializationDegradedPartitionedMetaFragment
        ...AssetHealthMaterializationHealthyPartitionedMetaFragment
        ...AssetHealthMaterializationDegradedNotPartitionedMetaFragment
      }
      assetChecksStatus
      assetChecksStatusMetadata {
        ...AssetHealthCheckDegradedMetaFragment
        ...AssetHealthCheckWarningMetaFragment
        ...AssetHealthCheckUnknownMetaFragment
      }
      freshnessStatus
      freshnessStatusMetadata {
        ...AssetHealthFreshnessMetaFragment
      }
    }
  }

  fragment AssetHealthMaterializationDegradedPartitionedMetaFragment on AssetHealthMaterializationDegradedPartitionedMeta {
    numMissingPartitions
    numFailedPartitions
    totalNumPartitions
  }

  fragment AssetHealthMaterializationHealthyPartitionedMetaFragment on AssetHealthMaterializationHealthyPartitionedMeta {
    numMissingPartitions
    totalNumPartitions
  }

  fragment AssetHealthMaterializationDegradedNotPartitionedMetaFragment on AssetHealthMaterializationDegradedNotPartitionedMeta {
    failedRunId
  }

  fragment AssetHealthCheckDegradedMetaFragment on AssetHealthCheckDegradedMeta {
    numFailedChecks
    numWarningChecks
    totalNumChecks
  }

  fragment AssetHealthCheckWarningMetaFragment on AssetHealthCheckWarningMeta {
    numWarningChecks
    totalNumChecks
  }

  fragment AssetHealthCheckUnknownMetaFragment on AssetHealthCheckUnknownMeta {
    numNotExecutedChecks
    totalNumChecks
  }

  fragment AssetHealthFreshnessMetaFragment on AssetHealthFreshnessMeta {
    lastMaterializedTimestamp
  }
  ${PYTHON_ERROR_FRAGMENT}
`;

// For tests
export function __resetForJest() {
  Object.assign(AssetHealthData, init());
}

function buildEmptyAssetHealthFragment(key: string): AssetHealthFragment {
  return {
    __typename: 'Asset',
    key: {
      __typename: 'AssetKey',
      ...tokenToAssetKey(key),
    },
    latestMaterializationTimestamp: null,
    latestFailedToMaterializeTimestamp: null,
    freshnessStatusChangedTimestamp: null,
    assetHealth: null,
  };
}
