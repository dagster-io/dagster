import {Box, Checkbox} from '@dagster-io/ui';
import * as React from 'react';

import {testId} from '../testing/testId';

import {partitionStatusToText} from './PartitionStatus';
import {AssetPartitionStatus} from './usePartitionHealthData';

export function countsByState(
  partitionKeysForCounts: {partitionKey: string; state: AssetPartitionStatus}[],
) {
  const result: {[state: string]: number} = {
    [AssetPartitionStatus.MATERIALIZED]: 0,
    [AssetPartitionStatus.MISSING]: 0,
    [AssetPartitionStatus.FAILED]: 0,
  };
  for (const key of partitionKeysForCounts) {
    result[key.state] = (result[key.state] || 0) + 1;
  }
  return result;
}

export const AssetPartitionStatusCheckboxes: React.FC<{
  counts: {[state: string]: number};
  value: AssetPartitionStatus[];
  allowed: AssetPartitionStatus[];
  onChange: (selected: AssetPartitionStatus[]) => void;
  disabled?: boolean;
}> = ({counts, value, onChange, allowed, disabled}) => {
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} style={{overflow: 'hidden'}}>
      {allowed.map((state) => (
        <Checkbox
          key={state}
          data-testid={testId(`partition-state-${state}-checkbox`)}
          disabled={disabled}
          style={{marginBottom: 0, marginLeft: 10, minWidth: 200}}
          checked={value.includes(state) && !disabled}
          label={`${partitionStatusToText(state)} (${counts[state]})`}
          onChange={() =>
            onChange(value.includes(state) ? value.filter((v) => v !== state) : [...value, state])
          }
        />
      ))}
    </Box>
  );
};
