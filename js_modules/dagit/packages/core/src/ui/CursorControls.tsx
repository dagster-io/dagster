import * as React from 'react';
import styled from 'styled-components/macro';

import {ButtonWIP} from './Button';
import {IconWIP} from './Icon';

export interface CursorPaginationProps {
  hasPrevCursor: boolean;
  hasNextCursor: boolean;
  popCursor: () => void;
  advanceCursor: () => void;
  reset: () => void;
}

export const CursorPaginationControls: React.FunctionComponent<CursorPaginationProps> = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
}) => {
  return (
    <CursorControlsContainer>
      <ButtonWIP disabled={!hasPrevCursor} icon={<IconWIP name="arrow_back" />} onClick={popCursor}>
        Previous
      </ButtonWIP>
      <ButtonWIP
        disabled={!hasNextCursor}
        icon={<IconWIP name="arrow_forward" />}
        onClick={advanceCursor}
      >
        Next
      </ButtonWIP>
    </CursorControlsContainer>
  );
};

export const CursorHistoryControls: React.FunctionComponent<CursorPaginationProps> = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
}) => {
  return (
    <CursorControlsContainer>
      <ButtonWIP
        icon={<IconWIP name="arrow_back" />}
        disabled={!hasNextCursor}
        onClick={advanceCursor}
      >
        <span className="hideable-button-text">Older</span>
      </ButtonWIP>
      <ButtonWIP
        rightIcon={<IconWIP name="arrow_forward" />}
        disabled={!hasPrevCursor}
        onClick={popCursor}
      >
        <span className="hideable-button-text">Newer</span>
      </ButtonWIP>
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
