import clsx from 'clsx';

import styles from './css/KeyboardTag.module.css';

interface KeyboardTagProps {
  withinTooltip?: boolean;
  children: React.ReactNode;
}

export const KeyboardTag = ({withinTooltip, children}: KeyboardTagProps) => (
  <div className={clsx(styles.keyboardTag, withinTooltip && styles.withinTooltip)}>{children}</div>
);
