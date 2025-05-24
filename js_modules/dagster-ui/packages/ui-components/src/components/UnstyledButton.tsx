import * as React from 'react';
import clsx from 'clsx';
import styles from './UnstyledButton.module.css';

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  $expandedClickPx?: number;
  $outlineOnHover?: boolean;
}

export const UnstyledButton = React.forwardRef<HTMLButtonElement, Props>(
  ({$expandedClickPx, $outlineOnHover, className, style, ...rest}, ref) => {
    const buttonStyle = React.useMemo(() => {
      if ($expandedClickPx) {
        return {
          ...style,
          '--expanded-click-px': `${$expandedClickPx}px`,
        };
      }
      return style;
    }, [style, $expandedClickPx]);

    return (
      <button
        ref={ref}
        className={clsx(
          styles.unstyledButton,
          $expandedClickPx ? styles.expandedClick : null,
          $outlineOnHover ? styles.outlineOnHover : null,
          className,
        )}
        style={buttonStyle}
        {...rest}
      />
    );
  },
);