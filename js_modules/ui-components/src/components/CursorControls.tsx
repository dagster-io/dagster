import clsx from 'clsx';
import {CSSProperties, forwardRef} from 'react';

import {Button} from './Button';
import {Icon} from './Icon';
import styles from './css/CursorControls.module.css';

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

export const CursorControlsContainer = forwardRef<
  HTMLDivElement,
  React.ComponentPropsWithRef<'div'>
>(({className, ...props}, ref) => {
  return (
    <div
      {...props}
      className={clsx(styles.cursorControlsContainer, 'dagster-cursor-controls', className)}
      ref={ref}
    />
  );
});
