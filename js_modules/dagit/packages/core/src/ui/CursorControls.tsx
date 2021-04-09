import {Button, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import styled from 'styled-components/macro';

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
      <Button style={{marginRight: 4}} disabled={!hasNextCursor} onClick={advanceCursor}>
        <Icon icon={IconNames.ARROW_LEFT} />
        <span className="hideable-button-text" style={{marginLeft: 8}}>
          Older
        </span>
      </Button>
      <Button style={{marginLeft: 4}} disabled={!hasPrevCursor} onClick={popCursor}>
        <span className="hideable-button-text" style={{marginRight: 8}}>
          Newer
        </span>
        <Icon icon={IconNames.ARROW_RIGHT} />
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
