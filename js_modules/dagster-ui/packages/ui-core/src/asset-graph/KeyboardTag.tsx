import clsx from 'clsx';
import styles from './KeyboardTag.module.css';

interface KeyboardTagProps {
  withinTooltip?: boolean;
  className?: string;
}

export const KeyboardTag = ({withinTooltip, className, ...rest}: KeyboardTagProps & React.HTMLAttributes<HTMLDivElement>) => {
  return (
    <div 
      className={clsx(
        styles.keyboardTag, 
        withinTooltip ? styles.withinTooltip : null,
        className
      )}
      {...rest}
    />
  );
};
