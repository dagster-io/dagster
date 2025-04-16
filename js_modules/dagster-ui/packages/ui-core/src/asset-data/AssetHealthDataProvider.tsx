import React from 'react';

import {ApolloClient, gql, useApolloClient} from '../apollo-client';
import {AssetBaseData} from './AssetBaseDataProvider';
import {tokenForAssetKey, tokenToAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {liveDataFactory} from '../live-data-provider/Factory';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {AssetHealthQuery, AssetHealthQueryVariables} from './types/AssetHealthDataProvider.types';

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

      const {data} = healthResponse;

      return Object.fromEntries(
        data.assetNodes.map((node) => [tokenForAssetKey(node.assetKey), node]),
      );
    },
  );
}
export const AssetHealthData = init();

export function useAssetHealthData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  const result = AssetHealthData.useLiveDataSingle(tokenForAssetKey(assetKey), thread);
  useBlockTraceUntilTrue('useAssetHealthData', !!result.liveData);
  return result;
}

export function useAssetsHealthData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'AssetHealth', // Use AssetHealth to get 250 batch size
) {
  const keys = React.useMemo(() => assetKeys.map((key) => tokenForAssetKey(key)), [assetKeys]);
  const result = AssetHealthData.useLiveData(keys, thread);
  AssetBaseData.useLiveData(keys, thread);
  useBlockTraceUntilTrue(
    'useAssetsHealthData',
    !!(Object.keys(result.liveDataByNode).length === assetKeys.length),
  );
  return result;
}

export const ASSETS_HEALTH_INFO_QUERY = gql`
  query AssetHealthQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      ...AssetHealthFragment
    }
  }

  fragment AssetHealthFragment on AssetNode {
    assetKey {
      path
    }

    assetHealth {
      assetHealth
      materializationStatus
      materializationStatusMetadata {
        ...AssetHealthMaterializationDegradedPartitionedMetaFragment
        ...AssetHealthMaterializationWarningPartitionedMetaFragment
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
    totalNumPartitions
  }

  fragment AssetHealthMaterializationWarningPartitionedMetaFragment on AssetHealthMaterializationWarningPartitionedMeta {
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
