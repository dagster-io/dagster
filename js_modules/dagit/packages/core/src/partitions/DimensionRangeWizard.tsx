import {Box, Button} from '@dagster-io/ui';
import * as React from 'react';

import {isTimeseriesPartition} from '../assets/MultipartitioningSupport';
import {Range} from '../assets/usePartitionHealthData';

import {DimensionRangeInput} from './DimensionRangeInput';
import {PartitionStatus} from './PartitionStatus';

export const DimensionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  partitionKeys: string[];
  ranges: Range[];
}> = ({selected, setSelected, partitionKeys, ranges}) => {
  const isTimeseries = isTimeseriesPartition(partitionKeys[0]);

  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          <DimensionRangeInput
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
          ranges={ranges}
          splitPartitions={!isTimeseries}
          selected={selected}
          onSelect={setSelected}
        />
      </Box>
    </>
  );
};
