import * as React from 'react';
import styled from 'styled-components/macro';

import {Box} from './Box';
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
    <Box
      margin={{top: 16}}
      flex={{direction: 'row', alignItems: 'center', gap: 12, justifyContent: 'center'}}
    >
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
    </Box>
  );
};

export const CursorHistoryControls: React.FunctionComponent<CursorPaginationProps> = ({
  hasPrevCursor,
  hasNextCursor,
  popCursor,
  advanceCursor,
}) => {
  return (
    <CursorHistoryControlsContainer>
      <ButtonWIP
        icon={<IconWIP name="arrow_back" />}
        style={{marginRight: 4}}
        disabled={!hasNextCursor}
        onClick={advanceCursor}
      >
        <span className="hideable-button-text">Older</span>
      </ButtonWIP>
      <ButtonWIP
        rightIcon={<IconWIP name="arrow_forward" />}
        style={{marginLeft: 4}}
        disabled={!hasPrevCursor}
        onClick={popCursor}
      >
        <span className="hideable-button-text">Newer</span>
      </ButtonWIP>
    </CursorHistoryControlsContainer>
  );
};

const CursorHistoryControlsContainer = styled.div`
  display: flex;
  align-items: center;

  @media (max-width: 1000px) {
    & .hideable-button-text {
      display: none;
    }
  }
`;
