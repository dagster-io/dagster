import {Checkbox, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

interface Props {
  checkedCount: number;
  totalCount: number;
  onToggleAll: (checked: boolean) => void;
}

export const CheckAllBox = ({checkedCount, totalCount, onToggleAll}: Props) => {
  return (
    <Tooltip content={`${checkedCount} of ${totalCount} selected`} placement="top">
      <Checkbox
        indeterminate={checkedCount > 0 && checkedCount !== totalCount}
        checked={checkedCount > 0 && checkedCount === totalCount}
        onChange={(e) => {
          if (e.target instanceof HTMLInputElement) {
            onToggleAll(checkedCount !== totalCount);
          }
        }}
      />
    </Tooltip>
  );
};
