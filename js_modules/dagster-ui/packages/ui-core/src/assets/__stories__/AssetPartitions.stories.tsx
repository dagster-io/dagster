import {MockedProvider} from '@apollo/client/testing';
import React from 'react';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {AssetPartitions} from '../AssetPartitions';
import {AssetViewParams} from '../AssetView';
import {
  MultiDimensionStaticPartitionHealthQuery,
  MultiDimensionTimeFirstPartitionHealthQuery,
  MultiDimensionTimeSecondPartitionHealthQuery,
  SingleDimensionStaticPartitionHealthQuery,
  SingleDimensionTimePartitionHealthQuery,
} from '../__fixtures__/PartitionHealthSummary.fixtures';

// eslint-disable-next-line import/no-default-export
export default {component: AssetPartitions};

export const SingleDimensionStaticAsset = () => {
  const [params, setParams] = React.useState<AssetViewParams>({});

  return (
    <StorybookProvider>
      <MockedProvider mocks={[SingleDimensionStaticPartitionHealthQuery]}>
        <AssetPartitions
          assetKey={{path: ['single_dimension_static']}}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['default']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const SingleDimensionTimeAsset = () => {
  const [params, setParams] = React.useState<AssetViewParams>({});

  return (
    <StorybookProvider>
      <MockedProvider mocks={[SingleDimensionTimePartitionHealthQuery]}>
        <AssetPartitions
          assetKey={{path: ['single_dimension_time']}}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['default']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const MultiDimensionStaticAsset = () => {
  const [params, setParams] = React.useState<AssetViewParams>({});

  return (
    <StorybookProvider>
      <MockedProvider mocks={[MultiDimensionStaticPartitionHealthQuery]}>
        <AssetPartitions
          assetKey={{path: ['multi_dimension_static']}}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['month', 'state']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const MultiDimensionTimeFirstAsset = () => {
  const [params, setParams] = React.useState<AssetViewParams>({});

  return (
    <StorybookProvider>
      <MockedProvider mocks={[MultiDimensionTimeFirstPartitionHealthQuery]}>
        <AssetPartitions
          assetKey={{path: ['multi_dimension_time_first']}}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['date', 'zstate']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
    </StorybookProvider>
  );
};

export const MultiDimensionTimeSecondAsset = () => {
  const [params, setParams] = React.useState<AssetViewParams>({});

  return (
    <StorybookProvider>
      <MockedProvider mocks={[MultiDimensionTimeSecondPartitionHealthQuery]}>
        <AssetPartitions
          assetKey={{path: ['multi_dimension_time_second']}}
          params={params}
          setParams={setParams}
          paramsTimeWindowOnly={false}
          assetPartitionDimensions={['astate', 'date']}
          dataRefreshHint={undefined}
        />
      </MockedProvider>
    </StorybookProvider>
  );
};
