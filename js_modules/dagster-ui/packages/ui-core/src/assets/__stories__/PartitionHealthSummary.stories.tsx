import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';

import {PartitionHealthSummary} from '../PartitionHealthSummary';
import {
  MultiDimensionStaticPartitionHealthQuery,
  MultiDimensionTimeFirstPartitionHealthQuery,
  MultiDimensionTimeSecondPartitionHealthQuery,
  SingleDimensionStaticPartitionHealthQuery,
  SingleDimensionTimePartitionHealthQuery,
} from '../__fixtures__/PartitionHealthSummary.fixtures';
import {AssetKey} from '../types';
import {usePartitionHealthData} from '../usePartitionHealthData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Assets/PartitionHealthSummary',
  component: PartitionHealthSummary,
};

const PartitionHealthSummaryWithData = ({
  assetKey,
}: {
  assetKey: AssetKey;
  ranges?: [string, string][];
}) => {
  const data = usePartitionHealthData([assetKey]);

  return (
    <Box style={{width: '50%'}}>
      <PartitionHealthSummary assetKey={assetKey} showAssetKey data={data} partitionStats={null} />
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
        <PartitionHealthSummaryWithData assetKey={{path: ['single_dimension_time']}} />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['single_dimension_static']}} />
        <PartitionHealthSummaryWithData assetKey={{path: ['single_dimension_static']}} />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_static']}} />
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_static']}} />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_first']}} />
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_first']}} />
      </Box>
      <Box flex={{direction: 'row', gap: 30}}>
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_second']}} />
        <PartitionHealthSummaryWithData assetKey={{path: ['multi_dimension_time_second']}} />
      </Box>
    </Box>
  </MockedProvider>
);
