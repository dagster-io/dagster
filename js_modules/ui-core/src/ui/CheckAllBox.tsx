import {Checkbox, Tooltip} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

interface Props {
  checkedCount: number;
  totalCount: number;
  onToggleAll: (checked: boolean) => void;
  size?: 'small' | 'large';
  label?: ReactNode;
}

export const CheckAllBox = ({
  checkedCount,
  totalCount,
  onToggleAll,
  size = 'large',
  label,
}: Props) => {
  return (
    <Tooltip
      content={`${checkedCount} of ${totalCount} selected`}
      placement="top"
      modifiers={{offset: {enabled: true, options: {offset: [0, 12]}}}}
    >
      <Checkbox
        size={size}
        indeterminate={checkedCount > 0 && checkedCount !== totalCount}
        checked={checkedCount > 0 && checkedCount === totalCount}
        onChange={(e) => {
          if (e.target instanceof HTMLInputElement) {
            onToggleAll(checkedCount !== totalCount);
          }
        }}
        label={label}
      />
    </Tooltip>
  );
};
