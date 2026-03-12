import clsx from 'clsx';
import {CSSProperties, forwardRef} from 'react';

import styles from './css/UnstyledButton.module.css';

interface Props extends React.ComponentPropsWithRef<'button'> {
  $expandedClickPx?: number;
  $outlineOnHover?: boolean;
}

export const UnstyledButton = forwardRef<HTMLButtonElement, Props>(
  ({$expandedClickPx, $outlineOnHover, className, style, ...props}, ref) => {
    const expandedStyle: CSSProperties | undefined = $expandedClickPx
      ? {padding: $expandedClickPx, margin: -$expandedClickPx, ...style}
      : style;

    return (
      <button
        {...props}
        className={clsx(styles.unstyledButton, $outlineOnHover && styles.outlineOnHover, className)}
        style={expandedStyle}
        ref={ref}
      />
    );
  },
);
