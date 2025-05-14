import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {featureEnabled} from '../app/Flags';
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
        healthResponse = {
          data: {
            assetsOrError: {nodes: [] as AssetHealthFragment[], __typename: 'AssetConnection'},
          },
        };
      }

      const {data} = healthResponse;
      switch (data.assetsOrError.__typename) {
        case 'PythonError':
          throw new Error('Python error');
        case 'AssetConnection':
          break;
        default:
          throw new Error('Unknown error');
      }

      const result: Record<string, AssetHealthFragment> = Object.fromEntries(
        data.assetsOrError.nodes.map((node) => [tokenForAssetKey(node.key), node]),
      );

      // External assets are not included in the health response, so as a workaround we add them with a null assetHealth
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
`;

// For tests
export function __resetForJest() {
  Object.assign(AssetHealthData, init());
}
