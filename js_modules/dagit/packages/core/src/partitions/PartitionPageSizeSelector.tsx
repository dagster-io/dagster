import {ButtonGroup, Button} from '@blueprintjs/core';
import * as React from 'react';

export const PartitionPageSizeSelector: React.FunctionComponent<{
  value: number | 'all' | undefined;
  onChange: (value: number | 'all') => void;
}> = ({value, onChange}) => {
  return (
    <ButtonGroup>
      {[7, 30, 120].map((size) => (
        <Button
          key={size}
          active={size === value}
          onClick={() => {
            onChange(size);
          }}
        >
          Last {size}
        </Button>
      ))}
      <Button
        active={value === 'all'}
        onClick={() => {
          onChange('all');
        }}
      >
        All
      </Button>
    </ButtonGroup>
  );
};
