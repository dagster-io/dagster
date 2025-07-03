import clsx from 'clsx';
import React from 'react';

import styles from './css/InsightsIdentifierDot.module.css';

interface InsightsIdentifierDotProps {
  color: string;
  className?: string;
  onClick?: React.MouseEventHandler<HTMLDivElement>;
}

export const InsightsIdentifierDot = ({
  color,
  className,
  onClick,
  ...rest
}: InsightsIdentifierDotProps) => {
  return (
    <div
      className={clsx(styles.insightsIdentifierDot, className)}
      style={{backgroundColor: color}}
      onClick={onClick}
      {...rest}
    />
  );
};
