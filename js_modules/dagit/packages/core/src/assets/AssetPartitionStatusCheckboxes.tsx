import {Box, Checkbox} from '@dagster-io/ui';
import * as React from 'react';

import {testId} from '../testing/testId';

import {AssetPartitionStatus, assetPartitionStatusToText} from './AssetPartitionStatus';

export const AssetPartitionStatusCheckboxes: React.FC<{
  counts: {[status: string]: number};
  value: AssetPartitionStatus[];
  allowed: AssetPartitionStatus[];
  onChange: (selected: AssetPartitionStatus[]) => void;
  disabled?: boolean;
}> = ({counts, value, onChange, allowed, disabled}) => {
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} style={{overflow: 'hidden'}}>
      {allowed.map((status) => (
        <Checkbox
          key={status}
          data-testid={testId(`partition-status-${status}-checkbox`)}
          disabled={disabled}
          style={{marginBottom: 0, marginLeft: 10, minWidth: 200}}
          checked={value.includes(status) && !disabled}
          label={`${assetPartitionStatusToText(status)} (${counts[status]})`}
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
