import {Box, NonIdealState} from '@dagster-io/ui-components';
import {useState} from 'react';

import {useAssetCheckPartitionData} from './useAssetCheckPartitionData';
import {AssetPartitionList} from '../AssetPartitionList';
import {AssetPartitionStatus} from '../AssetPartitionStatus';
import {AssetKey} from '../types';

interface AssetCheckPartitionsProps {
  assetKey: AssetKey;
  checkName: string;
}

export const AssetCheckPartitions = ({assetKey, checkName}: AssetCheckPartitionsProps) => {
  const {data: partitionData, loading} = useAssetCheckPartitionData(assetKey, checkName);
  const [focusedPartitionKey, setFocusedPartitionKey] = useState<string | undefined>();

  if (loading) {
    return (
      <Box padding={32}>
        <NonIdealState title="Loading partitions..." icon="hourglass" />
      </Box>
    );
  }

  if (!partitionData || partitionData.partitions.length === 0) {
    return (
      <Box padding={32}>
        <NonIdealState
          title="No partition data available"
          description="This asset check does not have partition information or no partitions exist."
          icon="partition"
        />
      </Box>
    );
  }

  const statusForPartition = (dimensionKey: string): AssetPartitionStatus[] => {
    return partitionData.statusForPartition(dimensionKey);
  };

  return (
    <Box flex={{direction: 'column', grow: 1}}>
      <AssetPartitionList
        partitions={partitionData.partitions}
        statusForPartition={statusForPartition}
        focusedDimensionKey={focusedPartitionKey}
        setFocusedDimensionKey={setFocusedPartitionKey}
      />
    </Box>
  );
};
