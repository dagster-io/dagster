import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {featureEnabled} from '../app/Flags';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {tokenForAssetKey, tokenToAssetKey} from '../asset-graph/Utils';
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

function init() {
  return liveDataFactory(
    () => {
      return useApolloClient();
    },
    async (keys, client: ApolloClient<any>) => {
      const assetKeys = keys.map(tokenToAssetKey);

      let healthResponse;
      if (featureEnabled(FeatureFlag.flagUseNewObserveUIs)) {
        healthResponse = await client.query<AssetHealthQuery, AssetHealthQueryVariables>({
          query: ASSETS_HEALTH_INFO_QUERY,
          fetchPolicy: 'no-cache',
          variables: {
            assetKeys,
          },
        });
      } else {
        return {};
      }

      const assetData = healthResponse.data.assetsOrError;
      if (assetData.__typename === 'PythonError') {
        showCustomAlert({
          title: 'An error ocurred',
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
          title: 'An unknown error ocurred',
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

export function useAssetsHealthData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'AssetHealth', // Use AssetHealth to get 250 batch size
) {
  const keys = memoizedAssetKeys(featureEnabled(FeatureFlag.flagUseNewObserveUIs) ? assetKeys : []);
  const result = AssetHealthData.useLiveData(keys, thread);
  useBlockTraceUntilTrue(
    'useAssetsHealthData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
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
