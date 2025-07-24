import {Box, Caption, Spinner} from '@dagster-io/ui-components';
import {memo, useCallback} from 'react';
import {useHistory} from 'react-router-dom';

import {isTimeseriesDimension} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {PartitionHealthData} from './usePartitionHealthData';
import {LiveDataForNode, displayNameForAssetKey} from '../asset-graph/Utils';
import {PartitionStatus} from '../partitions/PartitionStatus';
import {assetDetailsPathForKey} from '../assets/assetDetailsPathForKey';

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

  const handlePartitionInteraction = useCallback((selectedPartitions: string[]) => {
    if (selectedPartitions.length > 0) {
      const firstPartition = selectedPartitions[0]!;
      const lastPartition = selectedPartitions[selectedPartitions.length - 1]!;

      let defaultRange: string;
      let queryParams: {view: string; default_range: string; partition?: string};

      if (selectedPartitions.length === 1) {
        defaultRange = firstPartition;
        queryParams = {
          view: 'partitions',
          default_range: defaultRange,
          partition: firstPartition,
        };
      } else {
        defaultRange = `[${firstPartition}...${lastPartition}]`;
        queryParams = {
          view: 'partitions',
          default_range: defaultRange,
        };
      }

      const assetPath = assetDetailsPathForKey(assetKey, queryParams);
      history.push(assetPath);
    }
  }, [assetKey, history]);

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
              onSelect={(selectedPartitions) => handlePartitionInteraction(selectedPartitions)}
              onClick={(partitionName) => handlePartitionInteraction([partitionName])}
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
