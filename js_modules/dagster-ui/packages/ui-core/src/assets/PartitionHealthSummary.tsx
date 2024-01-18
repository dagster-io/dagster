import {Box, Caption, Spinner} from '@dagster-io/ui-components';
import {memo} from 'react';

import {AssetPartitionStatus} from './AssetPartitionStatus';
import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {PartitionDimensionSelection, PartitionHealthData} from './usePartitionHealthData';
import {displayNameForAssetKey} from '../asset-graph/Utils';
import {PartitionStatus} from '../partitions/PartitionStatus';

interface Props {
  assetKey: AssetKey;
  showAssetKey?: boolean;
  data: PartitionHealthData[];
  selections?: PartitionDimensionSelection[];
}

export const PartitionHealthSummary = memo((props: Props) => {
  const {showAssetKey, assetKey, data, selections} = props;
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
    <div>
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
            selected={selections ? selections[dimensionIdx]!.selectedKeys : undefined}
            health={{
              ranges: assetData.rangesForSingleDimension(
                dimensionIdx,
                selections?.length === 2 ? selections[1 - dimensionIdx]!.selectedRanges : undefined,
              ),
            }}
          />
        </Box>
      ))}
    </div>
  );
});
