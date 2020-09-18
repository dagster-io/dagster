import {Button} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';

import {CursorPaginationProps} from './runs/useCursorPaginatedQuery';

export const CursorPaginationControls: React.FunctionComponent<CursorPaginationProps> = ({
  hasPrevPage,
  hasNextPage,
  onPrevPage,
  onNextPage,
}) => {
  return (
    <div style={{textAlign: 'center', marginBottom: 10}}>
      <Button
        style={{
          visibility: hasPrevPage ? 'initial' : 'hidden',
          marginRight: 4,
        }}
        icon={IconNames.ARROW_LEFT}
        onClick={onPrevPage}
      >
        Prev Page
      </Button>
      <Button
        style={{
          visibility: hasNextPage ? 'initial' : 'hidden',
          marginLeft: 4,
        }}
        rightIcon={IconNames.ARROW_RIGHT}
        onClick={onNextPage}
      >
        Next Page
      </Button>
    </div>
  );
};
