import {Box, Button} from '@dagster-io/ui';
import * as React from 'react';

import {PartitionRangeInput} from './PartitionRangeInput';
import {PartitionState, PartitionStatus} from './PartitionStatus';

export const PartitionRangeWizard: React.FC<{
  selected: string[];
  setSelected: (selected: string[]) => void;
  all: string[];
  partitionData: {[name: string]: PartitionState};
}> = ({selected, setSelected, all, partitionData}) => {
  return (
    <>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 4}}>
        <Box flex={{direction: 'column'}} style={{flex: 1}}>
          <PartitionRangeInput value={selected} partitionNames={all} onChange={setSelected} />
        </Box>
        <Button small={true} onClick={() => setSelected(all.slice(-50))}>
          Last 50
        </Button>
        <Button small={true} onClick={() => setSelected(all.slice(-100))}>
          Last 100
        </Button>
        <Button small={true} onClick={() => setSelected(all)}>
          Select All
        </Button>
      </Box>
      <Box margin={{bottom: 8}}>
        <PartitionStatus
          partitionNames={all}
          partitionData={partitionData}
          selected={selected}
          onSelect={setSelected}
        />
      </Box>
    </>
  );
};
