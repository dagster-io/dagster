import {gql, useQuery} from '../../apollo-client';
import {METADATA_ENTRY_FRAGMENT} from '../../metadata/MetadataEntryFragment';
import {AssetKey} from '../types';
import {
  AssetCheckPartitionDetailQuery,
  AssetCheckPartitionDetailQueryVariables,
} from './types/useAssetCheckPartitionDetail.types';

export function useAssetCheckPartitionDetail(
  assetKey: AssetKey | null,
  checkName: string | null,
  partitionKey: string | null,
) {
  const queryResult = useQuery<
    AssetCheckPartitionDetailQuery,
    AssetCheckPartitionDetailQueryVariables
  >(ASSET_CHECK_PARTITION_DETAIL_QUERY, {
    variables: {
      assetKey: assetKey ? {path: assetKey.path} : {path: []},
      checkName: checkName || '',
      partitionKey: partitionKey || '',
    },
    skip: !assetKey || !checkName || !partitionKey,
  });

  return queryResult;
}

export const ASSET_CHECK_PARTITION_DETAIL_QUERY = gql`
  query AssetCheckPartitionDetailQuery(
    $assetKey: AssetKeyInput!
    $checkName: String!
    $partitionKey: String!
  ) {
    assetCheckExecutions(
      assetKey: $assetKey
      checkName: $checkName
      partition: $partitionKey
      limit: 10
    ) {
      id
      runId
      status
      timestamp
      stepKey
      evaluation {
        timestamp
        severity
        description
        success
        partition
        targetMaterialization {
          timestamp
          runId
        }
        metadataEntries {
          ...MetadataEntryFragment
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
