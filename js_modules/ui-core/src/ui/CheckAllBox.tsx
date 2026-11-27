import {Checkbox, Tooltip} from '@dagster-io/ui-components';
import {ReactNode} from 'react';

interface CheckAllBoxProps {
  checkedCount: number;
  totalCount: number;
  onToggleAll: (checked: boolean) => void;
  size?: 'small' | 'large';
  label?: ReactNode;
  className?: string;
  'aria-label'?: string;
}

export const CheckAllBox = ({
  checkedCount,
  totalCount,
  onToggleAll,
  size = 'large',
  label,
  className,
  'aria-label': ariaLabel,
}: CheckAllBoxProps) => {
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
        className={className}
        aria-label={ariaLabel}
      />
    </Tooltip>
  );
};
