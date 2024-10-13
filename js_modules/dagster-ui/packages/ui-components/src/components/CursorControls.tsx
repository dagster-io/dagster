import styled, {CSSProperties} from 'styled-components';

import {Button} from './Button';
import {Icon} from './Icon';

export interface CursorPaginationProps {
  hasPrevCursor: boolean;
  hasNextCursor: boolean;
  popCursor: () => void;
  advanceCursor: () => void;
  reset: () => void;
  style?: CSSProperties;
}

export const CursorPaginationControls = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
  style,
}: CursorPaginationProps) => {
  return (
    <CursorControlsContainer style={style}>
      <Button disabled={!hasPrevCursor} icon={<Icon name="arrow_back" />} onClick={popCursor}>
        Previous
      </Button>
      <Button
        disabled={!hasNextCursor}
        rightIcon={<Icon name="arrow_forward" />}
        onClick={advanceCursor}
      >
        Next
      </Button>
    </CursorControlsContainer>
  );
};

export const CursorHistoryControls = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
  style,
}: CursorPaginationProps) => {
  return (
    <CursorControlsContainer style={style}>
      <Button icon={<Icon name="arrow_back" />} disabled={!hasPrevCursor} onClick={popCursor}>
        <span className="hideable-button-text">Newer</span>
      </Button>
      <Button
        rightIcon={<Icon name="arrow_forward" />}
        disabled={!hasNextCursor}
        onClick={advanceCursor}
      >
        <span className="hideable-button-text">Older</span>
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
