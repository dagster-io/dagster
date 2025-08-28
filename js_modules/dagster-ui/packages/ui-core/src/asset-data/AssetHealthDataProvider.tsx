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
      const {allAssetKeys, loading} = useAllAssetsNodes();

      return {client: useApolloClient(), allAssetKeys, loading};
    },
    async (
      keys,
      {
        client,
        allAssetKeys,
        loading,
      }: {client: ApolloClient<any>; allAssetKeys: Set<string>; loading: boolean},
    ) => {
      if (loading) {
        // This is future proofing in case we somehow start requesting health data without having first loaded all assets nodes in the future
        // Today that doesn't happen in the app but if it ever does we'd basically just no-op every 500milliseconds until theyre loaded.
        // We need all of the assets keys to be loaded so that we can avoid making queries for assets that don't have definitions because
        // those queries are expensive.
        await new Promise((resolve) => setTimeout(resolve, 500));
        return {};
      }

      const assetKeys = keys.filter((key) => allAssetKeys.has(key)).map(tokenToAssetKey);

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
              assetMaterializations: [],
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
  const result = AssetHealthData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetHealthData', !!result.liveData);
  return result;
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
  const keys = memoizedAssetKeys(assetKeys);
  const result = AssetHealthData.useLiveData(keys, thread, skip);
  useBlockTraceUntilTrue(
    'useAssetsHealthData',
    !loading && (!blockTrace || !!(Object.keys(result.liveDataByNode).length === assetKeys.length)),
    {skip},
  );
  return result;
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

    assetMaterializations(limit: 1) {
      timestamp
    }

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
