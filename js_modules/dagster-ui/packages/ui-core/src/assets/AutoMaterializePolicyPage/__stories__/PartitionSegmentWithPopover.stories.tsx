import {Box} from '@dagster-io/ui-components';
import faker from 'faker';
import {useMemo} from 'react';

import {PartitionSegmentWithPopover} from '../PartitionSegmentWithPopover';
import {AssetConditionEvaluationStatus, AssetSubset} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Automaterialize/PartitionSegmentWithPopover',
  component: PartitionSegmentWithPopover,
};

const PARTITION_COUNT = 300;

export const TruePartitions = () => {
  const subset: AssetSubset = useMemo(() => {
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
        width={200}
        subset={subset}
      />
    </Box>
  );
};

export const FalsePartitions = () => {
  const subset: AssetSubset = useMemo(() => {
    const partitionKeys = new Array(PARTITION_COUNT)
      .fill(null)
      .map(() => faker.random.words(2).toLowerCase().replace(/ /g, '-'));
    return {
      assetKey: {path: ['foo', 'bar']},
      subsetValue: {
        boolValue: false,
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
        status={AssetConditionEvaluationStatus.FALSE}
        width={200}
        subset={subset}
      />
    </Box>
  );
};

export const SkippedPartitions = () => {
  const subset: AssetSubset = useMemo(() => {
    const partitionKeys = new Array(PARTITION_COUNT)
      .fill(null)
      .map(() => faker.random.words(2).toLowerCase().replace(/ /g, '-'));
    return {
      assetKey: {path: ['foo', 'bar']},
      subsetValue: {
        boolValue: null,
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
        status={AssetConditionEvaluationStatus.SKIPPED}
        width={200}
        subset={subset}
      />
    </Box>
  );
};

export const FewPartitions = () => {
  const subset: AssetSubset = useMemo(() => {
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
        width={200}
        subset={subset}
      />
    </Box>
  );
};
