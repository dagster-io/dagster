import {Box, Heading, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {AssetCheckStatusTag} from './AssetCheckStatusTag';
import {useAssetCheckPartitionData} from './useAssetCheckPartitionData';
import {AssetKey} from '../types';

interface AssetCheckPartitionDetailProps {
  assetKey: AssetKey;
  checkName: string;
  partitionKey: string;
}

export const AssetCheckPartitionDetail = ({
  assetKey,
  checkName,
  partitionKey,
}: AssetCheckPartitionDetailProps) => {
  const {data: partitionData, loading} = useAssetCheckPartitionData(assetKey, checkName);

  const partitionStatus = useMemo(() => {
    if (!partitionData) {
      return null;
    }
    return partitionData.statusForPartition(partitionKey);
  }, [partitionData, partitionKey]);

  if (loading || !partitionData) {
    return (
      <Box
        flex={{direction: 'column', justifyContent: 'center', alignItems: 'center'}}
        style={{height: '100%'}}
      >
        <Spinner purpose="section" />
      </Box>
    );
  }

  if (!partitionStatus) {
    return (
      <Box padding={24}>
        <NonIdealState
          title="Partition not found"
          description={`No data available for partition "${partitionKey}"`}
          icon="partition"
        />
      </Box>
    );
  }

  return (
    <Box padding={24}>
      <Box flex={{direction: 'column', gap: 16}}>
        <Heading>{partitionKey}</Heading>

        <Box flex={{direction: 'column', gap: 12}}>
          <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
            <strong>Status:</strong>
            {/* Mock execution for status display */}
            <AssetCheckStatusTag
              execution={
                {
                  status: partitionStatus[0],
                  evaluation: null,
                } as any
              }
            />
          </Box>

          <Box flex={{direction: 'column', gap: 8}}>
            <Box style={{color: '#666', fontSize: '14px'}}>
              Latest check execution details for this partition will be displayed here once the
              partition detail query is implemented.
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};
