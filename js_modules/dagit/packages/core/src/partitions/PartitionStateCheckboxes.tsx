import {Box, Checkbox} from '@dagster-io/ui';
import * as React from 'react';

import {PartitionState, partitionStatusToText} from './PartitionStatus';

export const PartitionStateCheckboxes: React.FC<{
  partitionKeysForCounts: {partitionKey: string; state: PartitionState}[];
  value: PartitionState[];
  allowed: PartitionState[];
  onChange: (selected: PartitionState[]) => void;
}> = ({partitionKeysForCounts, value, onChange, allowed}) => {
  const byState = React.useMemo(() => {
    const result: {[state: string]: number} = {
      [PartitionState.SUCCESS]: 0,
      [PartitionState.SUCCESS_MISSING]: 0,
      [PartitionState.MISSING]: 0,
      [PartitionState.FAILURE]: 0,
      [PartitionState.QUEUED]: 0,
      [PartitionState.STARTED]: 0,
    };
    for (const key of partitionKeysForCounts) {
      result[key.state] = (result[key.state] || 0) + 1;
    }
    return result;
  }, [partitionKeysForCounts]);

  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} style={{overflow: 'hidden'}}>
      {allowed.map((state) => (
        <Checkbox
          key={state}
          style={{marginBottom: 0, marginLeft: 10, minWidth: 200}}
          checked={value.includes(state)}
          label={`${partitionStatusToText(state)} (${byState[state]})`}
          onChange={() =>
            onChange(value.includes(state) ? value.filter((v) => v !== state) : [...value, state])
          }
        />
      ))}
    </Box>
  );
};
