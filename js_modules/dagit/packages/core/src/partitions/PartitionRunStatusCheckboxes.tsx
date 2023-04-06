import {Box, Checkbox} from '@dagster-io/ui';
import * as React from 'react';

import {RunStatus} from '../graphql/types';
import {runStatusToBackfillStateString} from '../runs/RunStatusTag';
import {testId} from '../testing/testId';

export function countsByState(partitionKeysForCounts: {partitionKey: string; state: RunStatus}[]) {
  const result: {[status: string]: number} = {
    [RunStatus.SUCCESS]: 0,
    [RunStatus.NOT_STARTED]: 0,
    [RunStatus.FAILURE]: 0,
    [RunStatus.QUEUED]: 0,
    [RunStatus.STARTED]: 0,
  };
  for (const key of partitionKeysForCounts) {
    result[key.state] = (result[key.state] || 0) + 1;
  }
  return result;
}

export const PartitionRunStatusCheckboxes: React.FC<{
  counts: {[status: string]: number};
  value: RunStatus[];
  allowed: RunStatus[];
  onChange: (selected: RunStatus[]) => void;
  disabled?: boolean;
}> = ({counts, value, onChange, allowed, disabled}) => {
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} style={{overflow: 'hidden'}}>
      {allowed.map((status) => (
        <Checkbox
          key={status}
          data-testid={testId(`run-status-${status}-checkbox`)}
          disabled={disabled}
          style={{marginBottom: 0, marginLeft: 10, minWidth: 200}}
          checked={value.includes(status) && !disabled}
          label={`${runStatusToBackfillStateString(status)} (${counts[status]})`}
          onChange={() =>
            onChange(
              value.includes(status) ? value.filter((v) => v !== status) : [...value, status],
            )
          }
        />
      ))}
    </Box>
  );
};
