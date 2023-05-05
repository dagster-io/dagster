import {Spinner, Box, Colors, Caption} from '@dagster-io/ui';
import React from 'react';

import {displayNameForAssetKey} from '../asset-graph/Utils';
import {PartitionStatus} from '../partitions/PartitionStatus';

import {AssetPartitionStatus} from './AssetPartitionStatus';
import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {PartitionHealthData, PartitionDimensionSelection} from './usePartitionHealthData';

export const PartitionHealthSummary: React.FC<{
  assetKey: AssetKey;
  showAssetKey?: boolean;
  data: PartitionHealthData[];
  selections?: PartitionDimensionSelection[];
}> = React.memo(({showAssetKey, assetKey, data, selections}) => {
  const assetData = data.find((d) => JSON.stringify(d.assetKey) === JSON.stringify(assetKey));

  if (!assetData) {
    return (
      <div style={{minHeight: 55, position: 'relative'}}>
        <Spinner purpose="section" />
      </div>
    );
  }

  const keysForTotals = selections
    ? selections.map((r) => r.selectedKeys)
    : assetData.dimensions.map((d) => d.partitionKeys);

  const total = keysForTotals.reduce((total, d) => d.length * total, 1);

  const success = keysForTotals
    .reduce(
      (combinations, d) =>
        combinations.length
          ? combinations.flatMap((keys) => d.map((key) => [...keys, key]))
          : d.map((key) => [key]),
      [] as string[][],
    )
    .filter((dkeys) => assetData.stateForKey(dkeys) === AssetPartitionStatus.MATERIALIZED).length;

  return (
    <Box color={Colors.Gray500}>
      <Box flex={{justifyContent: 'space-between'}} style={{fontWeight: 600}} margin={{bottom: 4}}>
        <Caption>{showAssetKey ? displayNameForAssetKey(assetKey) : 'Materialized'}</Caption>
        <Caption>{`${success.toLocaleString()}/${total.toLocaleString()}`}</Caption>
      </Box>
      {assetData.dimensions.map((dimension, dimensionIdx) => (
        <Box key={dimensionIdx} margin={{bottom: 4}}>
          {assetData.dimensions.length > 1 && <Caption>{dimension.name}</Caption>}
          <PartitionStatus
            small
            partitionNames={dimension.partitionKeys}
            splitPartitions={!isTimeseriesDimension(dimension)}
            selected={selections ? selections[dimensionIdx].selectedKeys : undefined}
            health={{
              ranges: assetData.rangesForSingleDimension(
                dimensionIdx,
                selections?.length === 2 ? selections[1 - dimensionIdx].selectedRanges : undefined,
              ),
            }}
          />
        </Box>
      ))}
    </Box>
  );
});
