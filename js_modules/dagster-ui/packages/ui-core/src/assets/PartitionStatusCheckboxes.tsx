import {Box, Checkbox} from '@dagster-io/ui-components';

import {testId} from '../testing/testId';

export interface PartitionStatusCheckboxesProps<TStatus> {
  counts: {[status: string]: number};
  value: TStatus[];
  onChange: (selected: TStatus[]) => void;
  allowed: TStatus[];
  statusToText: (status: TStatus) => string;
  disabled?: boolean;
}

export function PartitionStatusCheckboxes<TStatus>({
  counts,
  value,
  onChange,
  allowed,
  statusToText,
  disabled,
}: PartitionStatusCheckboxesProps<TStatus>) {
  return (
    <Box flex={{direction: 'row', alignItems: 'center', gap: 12}} style={{overflow: 'hidden'}}>
      {allowed.map((status) => (
        <Checkbox
          key={String(status)}
          data-testid={testId(`partition-status-${String(status)}-checkbox`)}
          disabled={disabled}
          style={{marginBottom: 0, marginLeft: 10, minWidth: 200}}
          checked={value.includes(status) && !disabled}
          label={`${statusToText(status)} (${counts[String(status)] || 0})`}
          onChange={() =>
            onChange(
              value.includes(status) ? value.filter((v) => v !== status) : [...value, status],
            )
          }
        />
      ))}
    </Box>
  );
}
