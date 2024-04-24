import {Box} from '@dagster-io/ui-components';
import faker from 'faker';
import {useMemo} from 'react';

import {AssetConditionEvaluationStatus} from '../../../graphql/types';
import {PartitionSegmentWithPopover} from '../PartitionSegmentWithPopover';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/PartitionSegmentWithPopover',
  component: PartitionSegmentWithPopover,
};

const PARTITION_COUNT = 300;

export const TruePartitions = () => {
  const subset = useMemo(() => {
    const partitionKeys = new Array(PARTITION_COUNT)
      .fill(null)
      .map(() => faker.random.words(2).toLowerCase().replace(/ /g, '-'));
    return {
      assetKey: {path: ['foo', 'bar']},
      subsetValue: {
        boolValue: true,
        partitionKeys,
        partitionKeyRanges: null,
        isPartitioned: true,
      },
    };
  }, []);

  return (
    <Box flex={{direction: 'row'}}>
      <PartitionSegmentWithPopover
        description="is_missing"
        status={AssetConditionEvaluationStatus.TRUE}
        subset={subset}
        selectPartition={() => {}}
      />
    </Box>
  );
};

export const FewPartitions = () => {
  const subset = useMemo(() => {
    const partitionKeys = new Array(2)
      .fill(null)
      .map(() => faker.random.words(2).toLowerCase().replace(/ /g, '-'));
    return {
      assetKey: {path: ['foo', 'bar']},
      subsetValue: {
        boolValue: true,
        partitionKeys,
        partitionKeyRanges: null,
        isPartitioned: true,
      },
    };
  }, []);

  return (
    <Box flex={{direction: 'row'}}>
      <PartitionSegmentWithPopover
        description="is_missing"
        status={AssetConditionEvaluationStatus.TRUE}
        subset={subset}
        selectPartition={() => {}}
      />
    </Box>
  );
};
