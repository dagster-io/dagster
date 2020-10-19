import {Button} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

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
          visibility: hasPrevCursor ? 'initial' : 'hidden',
          marginRight: 4,
        }}
        icon={IconNames.ARROW_LEFT}
        onClick={popCursor}
      >
        Prev Page
      </Button>
      <Button
        style={{
          visibility: hasNextCursor ? 'initial' : 'hidden',
          marginLeft: 4,
        }}
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
    <div style={{textAlign: 'center'}}>
      <Button
        style={{marginRight: 4}}
        disabled={!hasNextCursor}
        icon={IconNames.ARROW_LEFT}
        onClick={advanceCursor}
      >
        Older
      </Button>
      <Button
        style={{marginLeft: 4}}
        disabled={!hasPrevCursor}
        rightIcon={IconNames.ARROW_RIGHT}
        onClick={popCursor}
      >
        Newer
      </Button>
    </div>
  );
};
