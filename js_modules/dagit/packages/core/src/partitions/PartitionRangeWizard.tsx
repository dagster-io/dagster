import {Box, Button} from '@dagster-io/ui';
import * as React from 'react';

import {isTimeseriesPartition} from '../assets/MultipartitioningSupport';

import {PartitionRangeInput} from './PartitionRangeInput';
import {PartitionState, PartitionStatus} from './PartitionStatus';

export const PartitionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  partitionStateForKey: (partitionKey: string, partitionIdx: number) => PartitionState;
}> = ({selected, setSelected, partitionKeys, partitionStateForKey}) => {
  const isTimeseries = isTimeseriesPartition(partitionKeys[0]);

  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          <PartitionRangeInput
            value={selected}
            partitionKeys={partitionKeys}
            onChange={setSelected}
            isTimeseries={isTimeseries}
          />
        </Box>
        {isTimeseries && (
          <Button small={true} onClick={() => setSelected(partitionKeys.slice(-1))}>
            Latest
          </Button>
        )}
        <Button small={true} onClick={() => setSelected(partitionKeys)}>
          All
        </Button>
      </Box>
      <Box margin={{bottom: 8}}>
        <PartitionStatus
          partitionNames={partitionKeys}
          partitionStateForKey={partitionStateForKey}
          splitPartitions={!isTimeseries}
          selected={selected}
          onSelect={setSelected}
        />
      </Box>
    </>
  );
};
