import styled, {CSSProperties} from 'styled-components';

import {Button} from './Button';
import {Icon} from './Icon';

export interface CursorPaginationProps {
  cursor?: string;
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
        上一页
      </Button>
      <Button
        disabled={!hasNextCursor}
        rightIcon={<Icon name="arrow_forward" />}
        onClick={advanceCursor}
      >
        下一页
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
        <span className="hideable-button-text">更新</span>
      </Button>
      <Button
        rightIcon={<Icon name="arrow_forward" />}
        disabled={!hasNextCursor}
        onClick={advanceCursor}
      >
        <span className="hideable-button-text">更早</span>
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
