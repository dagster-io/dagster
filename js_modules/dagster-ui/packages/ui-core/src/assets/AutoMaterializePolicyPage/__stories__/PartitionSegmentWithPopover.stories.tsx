import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';

import {PartitionSegmentWithPopover} from '../PartitionSegmentWithPopover';
import {
  SAMPLE_ASSET_KEY_PATH,
  SAMPLE_EVALUATION_ID,
  SAMPLE_MANY_PARTITIONS_COUNT,
  SAMPLE_NODE_UNIQUE_ID,
  SAMPLE_PARTITION_KEYS,
  buildHasFewPartitions,
  buildHasManyPartitions,
} from '../__fixtures__/PartitionSegmentWithPopover.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/PartitionSegmentWithPopover',
  component: PartitionSegmentWithPopover,
};

export const FewPartitions = () => {
  return (
    <MockedProvider mocks={[buildHasFewPartitions(2000)]}>
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{width: '100%'}}>
        <PartitionSegmentWithPopover
          description="is_missing"
          assetKeyPath={SAMPLE_ASSET_KEY_PATH}
          evaluationId={SAMPLE_EVALUATION_ID}
          nodeUniqueId={SAMPLE_NODE_UNIQUE_ID}
          numTrue={SAMPLE_PARTITION_KEYS.length}
          selectPartition={() => {}}
        />
      </Box>
    </MockedProvider>
  );
};

export const ManyPartitions = () => {
  const mocks = buildHasManyPartitions({
    delayMsec: 2000,
    partitionCount: SAMPLE_MANY_PARTITIONS_COUNT,
  });
  return (
    <MockedProvider mocks={[mocks]}>
      <Box flex={{direction: 'row', justifyContent: 'center'}} style={{width: '100%'}}>
        <PartitionSegmentWithPopover
          description="is_missing"
          assetKeyPath={SAMPLE_ASSET_KEY_PATH}
          evaluationId={SAMPLE_EVALUATION_ID}
          nodeUniqueId={SAMPLE_NODE_UNIQUE_ID}
          numTrue={SAMPLE_MANY_PARTITIONS_COUNT}
          selectPartition={() => {}}
        />
      </Box>
    </MockedProvider>
  );
};
