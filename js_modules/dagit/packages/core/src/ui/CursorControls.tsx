import {Button} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

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
    <div style={{textAlign: 'center', marginBottom: 10}}>
      <Button
        style={{
          marginRight: 4,
        }}
        disabled={!hasPrevCursor}
        icon={IconNames.ARROW_LEFT}
        onClick={popCursor}
      >
        Prev Page
      </Button>
      <Button
        style={{
          marginLeft: 4,
        }}
        disabled={!hasNextCursor}
        rightIcon={IconNames.ARROW_RIGHT}
        onClick={advanceCursor}
      >
        Next Page
      </Button>
    </div>
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
      <Button
        icon={<IconWIP name="arrow_back" />}
        style={{marginRight: 4}}
        disabled={!hasNextCursor}
        onClick={advanceCursor}
      >
        <span className="hideable-button-text">Older</span>
      </Button>
      <Button
        rightIcon={<IconWIP name="arrow_forward" />}
        style={{marginLeft: 4}}
        disabled={!hasPrevCursor}
        onClick={popCursor}
      >
        <span className="hideable-button-text">Newer</span>
      </Button>
    </CursorHistoryControlsContainer>
  );
};

const CursorHistoryControlsContainer = styled.div`
  text-align: center;
  white-space: nowrap;

  @media (max-width: 1000px) {
    & .hideable-button-text {
      display: none;
    }
  }
`;
