import {Box, Button, Checkbox} from '@dagster-io/ui';
import groupBy from 'lodash/groupBy';
import xor from 'lodash/xor';
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
      <Box margin={{top: 8}}>
        <PartitionStatus
          partitionNames={all}
          partitionData={partitionData}
          selected={selected}
          onSelect={setSelected}
        />
      </Box>
      <Box flex={{direction: 'row', alignItems: 'center', gap: 8}} padding={{vertical: 8}}>
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
    </>
  );
};

export const PartitionStateCheckboxes: React.FC<{
  partitionData: {[name: string]: PartitionState};
  partitionKeysForCounts: string[];
  value: PartitionState[];
  onChange: (selected: PartitionState[]) => void;
}> = ({partitionData, partitionKeysForCounts, value, onChange}) => {
  const byState = React.useMemo(() => {
    const result: {[state: string]: number} = {
      [PartitionState.SUCCESS]: 0,
      [PartitionState.FAILURE]: 0,
      [PartitionState.MISSING]: 0,
    };
    for (const key of Object.keys(partitionData)) {
      if (partitionKeysForCounts.includes(key)) {
        result[partitionData[key]] = (result[partitionData[key]] || 0) + 1;
      }
    }
    return result;
  }, [partitionData, partitionKeysForCounts]);

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
      <Checkbox
        style={{marginBottom: 0, marginLeft: 10}}
        checked={value.includes(PartitionState.SUCCESS)}
        label={`Succeeded (${byState[PartitionState.SUCCESS]})`}
        onChange={() => onChange(xor(value, [PartitionState.SUCCESS]))}
      />
      <Checkbox
        style={{marginBottom: 0, marginLeft: 10}}
        checked={value.includes(PartitionState.FAILURE)}
        label={`Failed (${byState[PartitionState.FAILURE]})`}
        onChange={() => onChange(xor(value, [PartitionState.FAILURE]))}
      />
      <Checkbox
        style={{marginBottom: 0, marginLeft: 10}}
        checked={value.includes(PartitionState.MISSING)}
        label={`Missing (${byState[PartitionState.MISSING]})`}
        onChange={() => onChange(xor(value, [PartitionState.MISSING]))}
      />
    </Box>
  );
};
