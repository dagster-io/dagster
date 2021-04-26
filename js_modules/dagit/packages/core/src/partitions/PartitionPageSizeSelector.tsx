import {ButtonGroup, Button} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

export const PartitionPageSizeSelector: React.FunctionComponent<{
  value: number | 'all' | undefined;
  onChange: (value: number | 'all') => void;
}> = ({value, onChange}) => {
  return (
    <PartitionPageSizeButtonGroup>
      {[7, 30, 120].map((size) => (
        <Button
          key={size}
          active={size === value}
          onClick={() => {
            onChange(size);
          }}
        >
          <span className={size > 7 ? 'hideable-button-text' : ''}>Last </span>
          {size}
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
    </PartitionPageSizeButtonGroup>
  );
};

const PartitionPageSizeButtonGroup = styled(ButtonGroup)`
  text-align: center;
  white-space: nowrap;

  @media (max-width: 1000px) {
    & .hideable-button-text {
      display: none;
    }
  }
`;
