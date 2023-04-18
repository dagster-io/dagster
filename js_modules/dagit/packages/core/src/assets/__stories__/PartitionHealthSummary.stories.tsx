import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui';
import React from 'react';

import {PartitionHealthSummary} from '../PartitionHealthSummary';
import {
  MultiDimensionStaticPartitionHealthQuery,
  MultiDimensionTimeFirstPartitionHealthQuery,
  MultiDimensionTimeSecondPartitionHealthQuery,
  SingleDimensionStaticPartitionHealthQuery,
  SingleDimensionTimePartitionHealthQuery,
} from '../__fixtures__/PartitionHealthSummary.fixtures';
import {AssetKey} from '../types';
import {PartitionDimensionSelection, usePartitionHealthData} from '../usePartitionHealthData';

// eslint-disable-next-line import/no-default-export
export default {
  component: PartitionHealthSummary,
};

const PartitionHealthSummaryWithData: React.FC<{
  assetKey: AssetKey;
  ranges?: [string, string][];
}> = ({assetKey, ranges}) => {
  const data = usePartitionHealthData([assetKey]);

  // Convert the convenient test shorthand into a PartitionDimensionSelection
  const selections =
    data[0] && ranges
      ? ranges.map((range, idx) => {
          const dim = data[0].dimensions[idx]!;
          const idx0 = dim.partitionKeys.indexOf(range[0]);
          const idx1 = dim.partitionKeys.indexOf(range[1]);
          return {
            dimension: dim,
            selectedKeys: dim.partitionKeys.slice(idx0, idx1 + 1),
            selectedRanges: [{start: {idx: idx0, key: range[0]}, end: {idx: idx1, key: range[1]}}],
          } as PartitionDimensionSelection;
        })
      : undefined;

  return (
    <Box style={{width: '50%'}}>
      <PartitionHealthSummary
        assetKey={assetKey}
        showAssetKey
        data={data}
        selections={selections}
      />
    </Box>
  );
};

const MOCKS = [
  SingleDimensionTimePartitionHealthQuery,
  SingleDimensionStaticPartitionHealthQuery,
  MultiDimensionStaticPartitionHealthQuery,
  MultiDimensionTimeFirstPartitionHealthQuery,
  MultiDimensionTimeSecondPartitionHealthQuery,
];

export const States = () => (
  <MockedProvider mocks={MOCKS}>
    <Box flex={{direction: 'column', gap: 60}}>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['single_dimension_time']}} />
        <PartitionHealthSummaryWithData
          assetKey={{path: ['single_dimension_time']}}
          ranges={[['2023-01-01-00:00', '2023-02-01-00:00']]}
        />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['single_dimension_static']}} />
        <PartitionHealthSummaryWithData
          assetKey={{path: ['single_dimension_static']}}
          ranges={[['KY', 'FL']]}
        />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_static']}} />
        <PartitionHealthSummaryWithData
          assetKey={{path: ['multi_dimension_static']}}
          ranges={[
            ['May', 'May'],
            ['TN', 'VA'],
          ]}
        />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_first']}} />
        <PartitionHealthSummaryWithData
          assetKey={{path: ['multi_dimension_time_first']}}
          ranges={[
            ['2022-09-10', '2022-09-16'],
            ['TN', 'VA'],
          ]}
        />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_second']}} />
        <PartitionHealthSummaryWithData
          assetKey={{path: ['multi_dimension_time_second']}}
          ranges={[
            ['TN', 'VA'],
            ['2022-09-28', '2022-11-16'],
          ]}
        />
      </Box>
    </Box>
  </MockedProvider>
);
