import {Box, Spinner, Text} from '@dagster-io/ui-components';
import {memo, useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {isTimeBasedPartition, isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey, AssetViewParams} from './types';
import {PartitionHealthData, PartitionHealthDimension} from './usePartitionHealthData';
import {LiveDataForNode, displayNameForAssetKey} from '../asset-graph/Utils';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';
import {PartitionStatus} from '../partitions/PartitionStatus';
import {escapePartitionKey, serializeRange} from '../partitions/SpanRepresentation';

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
        defaultRange = escapePartitionKey(firstPartition);
        queryParams = {
          view: 'partitions',
          partition: firstPartition,
          default_range: defaultRange,
        };
      } else {
        defaultRange = serializeRange(firstPartition, lastPartition);
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
      <Box flex={{justifyContent: 'space-between'}} margin={{bottom: 4}}>
        <Text size={12} weight={600}>
          {showAssetKey ? displayNameForAssetKey(assetKey) : 'Materialized'}
        </Text>
        {partitionStats ? (
          <Text size={12} weight={600}>
            {`${partitionStats.numMaterialized.toLocaleString()}/${partitionStats.numPartitions.toLocaleString()}`}
          </Text>
        ) : null}
      </Box>
      {!assetData ? (
        <Box padding={{vertical: 12}}>
          <Spinner purpose="section" />
        </Box>
      ) : (
        assetData.dimensions.map((dimension, dimensionIdx) => (
          <Box key={dimensionIdx} margin={{bottom: 4}}>
            {assetData.dimensions.length > 1 && <Text size={12}>{dimension.name}</Text>}
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
