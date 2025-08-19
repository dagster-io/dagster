import {Box, Caption, Spinner} from '@dagster-io/ui-components';
import {memo, useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {isTimeBasedPartition, isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey, AssetViewParams} from './types';
import {PartitionHealthData, PartitionHealthDimension} from './usePartitionHealthData';
import {LiveDataForNode, displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {PartitionStatus} from '../partitions/PartitionStatus';

interface Props {
  assetKey: AssetKey;
  showAssetKey?: boolean;
  data: PartitionHealthData[];
  partitionStats: LiveDataForNode['partitionStats'] | undefined;
}

export const PartitionHealthSummary = memo((props: Props) => {
  const {showAssetKey, assetKey, data, partitionStats} = props;
  const assetData = data.find(
    (d) => JSON.stringify(d.assetKey.path) === JSON.stringify(assetKey.path),
  );
  const history = useHistory();

  const handlePartitionInteraction = useCallback(
    (selectedPartitions: string[], dimension?: PartitionHealthDimension) => {
      const firstPartition = selectedPartitions[0] ?? null;
      const lastPartition = selectedPartitions[selectedPartitions.length - 1] ?? null;

      if (!firstPartition || !lastPartition) {
        return;
      }

      let defaultRange: string;
      let queryParams: AssetViewParams;

      if (selectedPartitions.length === 1) {
        defaultRange = firstPartition;
        queryParams = {
          view: 'partitions',
          partition: firstPartition,
          default_range: defaultRange,
        };
      } else {
        defaultRange = `[${firstPartition}...${lastPartition}]`;
        queryParams = {
          view: 'partitions',
          ...(dimension && isTimeBasedPartition(dimension) ? {partition: lastPartition} : {}),
          default_range: defaultRange,
        };
      }

      const assetPath = assetDetailsPathForKey(assetKey, queryParams);
      history.push(assetPath);
    },
    [assetKey, history],
  );

  return (
    <div>
      <Box flex={{justifyContent: 'space-between'}} style={{fontWeight: 600}} margin={{bottom: 4}}>
        <Caption>{showAssetKey ? displayNameForAssetKey(assetKey) : 'Materialized'}</Caption>
        {partitionStats ? (
          <Caption>{`${partitionStats.numMaterialized.toLocaleString()}/${partitionStats.numPartitions.toLocaleString()}`}</Caption>
        ) : null}
      </Box>
      {!assetData ? (
        <Box padding={{vertical: 12}}>
          <Spinner purpose="section" />
        </Box>
      ) : (
        assetData.dimensions.map((dimension, dimensionIdx) => (
          <Box key={dimensionIdx} margin={{bottom: 4}}>
            {assetData.dimensions.length > 1 && <Caption>{dimension.name}</Caption>}
            <PartitionStatus
              small
              partitionNames={dimension.partitionKeys}
              splitPartitions={!isTimeseriesDimension(dimension)}
              selected={[]}
              onSelect={(selectedPartitions) =>
                handlePartitionInteraction(selectedPartitions, dimension)
              }
              onClick={(partitionName) => handlePartitionInteraction([partitionName], dimension)}
              health={{
                ranges: assetData.rangesForSingleDimension(dimensionIdx, undefined),
              }}
            />
          </Box>
        ))
      )}
    </div>
  );
});
