import * as React from 'react';
import styles from './Page.module.css';

export const Page: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => {
  const { children, className, ...rest } = props;
  return (
    <div className={className ? `${styles.page} ${className}` : styles.page} {...rest}>
      {children}
    </div>
  );
};
