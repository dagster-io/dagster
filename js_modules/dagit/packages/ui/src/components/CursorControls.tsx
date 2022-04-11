import * as React from 'react';
import styled from 'styled-components/macro';

import {Button} from './Button';
import {Icon} from './Icon';

export interface CursorPaginationProps {
  hasPrevCursor: boolean;
  hasNextCursor: boolean;
  popCursor: () => void;
  advanceCursor: () => void;
  reset: () => void;
}

export const CursorPaginationControls: React.FC<CursorPaginationProps> = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
}) => {
  return (
    <CursorControlsContainer>
      <Button disabled={!hasPrevCursor} icon={<Icon name="arrow_back" />} onClick={popCursor}>
        Previous
      </Button>
      <Button
        disabled={!hasNextCursor}
        icon={<Icon name="arrow_forward" />}
        onClick={advanceCursor}
      >
        Next
      </Button>
    </CursorControlsContainer>
  );
};

export const CursorHistoryControls: React.FC<CursorPaginationProps> = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
}) => {
  return (
    <CursorControlsContainer>
      <Button icon={<Icon name="arrow_back" />} disabled={!hasNextCursor} onClick={advanceCursor}>
        <span className="hideable-button-text">Older</span>
      </Button>
      <Button
        rightIcon={<Icon name="arrow_forward" />}
        disabled={!hasPrevCursor}
        onClick={popCursor}
      >
        <span className="hideable-button-text">Newer</span>
      </Button>
    </CursorControlsContainer>
  );
};

export const CursorControlsContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
`;
