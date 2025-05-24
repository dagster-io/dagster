import React from 'react';
import styles from './InsightsIdentifierDot.module.css';

interface InsightsIdentifierDotProps {
  color: string;
  className?: string;
  onClick?: React.MouseEventHandler<HTMLDivElement>;
}

export const InsightsIdentifierDot: React.FC<InsightsIdentifierDotProps> = ({
  color,
  className,
  onClick,
  ...rest
}) => {
  return (
    <div
      className={
        className ? `${styles.insightsIdentifierDot} ${className}` : styles.insightsIdentifierDot
      }
      style={{backgroundColor: color}}
      onClick={onClick}
      {...rest}
    />
  );
};
