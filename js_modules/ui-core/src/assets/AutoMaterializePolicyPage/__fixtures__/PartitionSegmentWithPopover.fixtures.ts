import {buildQueryMock} from '../../../testing/mocking';
import {PARTITION_SUBSET_LIST_QUERY} from '../PartitionSubsetListQuery';
import {
  PartitionSubsetListQuery,
  PartitionSubsetListQueryVariables,
} from '../types/PartitionSubsetListQuery.types';

export const SAMPLE_ASSET_KEY_PATH = ['foo', 'bar'];
export const SAMPLE_EVALUATION_ID = '1';
export const SAMPLE_NODE_UNIQUE_ID = 'a1b2c3';
export const SAMPLE_PARTITION_KEYS = ['partition-a', 'partition-b'];
export const SAMPLE_MANY_PARTITIONS_COUNT = 100000;

export const buildHasFewPartitions = (delayMsec: number = 0) => {
  return buildQueryMock<PartitionSubsetListQuery, PartitionSubsetListQueryVariables>({
    query: PARTITION_SUBSET_LIST_QUERY,
    variables: {
      assetKey: {path: SAMPLE_ASSET_KEY_PATH},
      evaluationId: SAMPLE_EVALUATION_ID,
      nodeUniqueId: SAMPLE_NODE_UNIQUE_ID,
    },
    data: {
      truePartitionsForAutomationConditionEvaluationNode: SAMPLE_PARTITION_KEYS,
    },
    delay: delayMsec,
  });
};

export const buildHasManyPartitions = ({
  delayMsec = 0,
  partitionCount,
}: {
  delayMsec?: number;
  partitionCount: number;
}) => {
  return buildQueryMock<PartitionSubsetListQuery, PartitionSubsetListQueryVariables>({
    query: PARTITION_SUBSET_LIST_QUERY,
    variables: {
      assetKey: {path: SAMPLE_ASSET_KEY_PATH},
      evaluationId: SAMPLE_EVALUATION_ID,
      nodeUniqueId: SAMPLE_NODE_UNIQUE_ID,
    },
    data: {
      truePartitionsForAutomationConditionEvaluationNode: new Array(partitionCount)
        .fill(null)
        .map((_, ii) => `${ii}`),
    },
    delay: delayMsec,
  });
};
