import {Box, SpinnerWithText} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {AssetMaterializationGraphs} from './AssetMaterializationGraphs';
import {useGroupedEvents} from './groupByPartition';
import {AssetKey, AssetViewParams} from './types';
import {useRecentAssetEvents} from './useRecentAssetEvents';

interface Props {
  assetKey?: AssetKey;
  params: AssetViewParams;
  assetHasDefinedPartitions: boolean;
}

export const AssetEventMetadataPlots = (props: Props) => {
  const {assetKey, params, assetHasDefinedPartitions} = props;
  const {materializations, observations, loadedPartitionKeys, loading, xAxis} =
    useRecentAssetEvents(assetKey, params, {assetHasDefinedPartitions});

  const grouped = useGroupedEvents(xAxis, materializations, observations, loadedPartitionKeys);
  const activeItems = useMemo(() => new Set([xAxis]), [xAxis]);
  console.log(activeItems);

  if (loading) {
    return (
      <Box padding={{vertical: 24}} flex={{direction: 'row', justifyContent: 'center'}}>
        <SpinnerWithText label="Loading plots…" />
      </Box>
    );
  }

  return <AssetMaterializationGraphs xAxis={xAxis} groups={grouped} />;
};
