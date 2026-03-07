import * as Progress from '@radix-ui/react-progress';
import clsx from 'clsx';

import {Colors} from './Color';
import styles from './css/ProgressBar.module.css';

interface ProgressBarProps {
  value: number; // 0-100
  animate?: boolean;
  fillColor?: string;
}

export const ProgressBar = (props: ProgressBarProps) => {
  const {value, animate = false, fillColor = Colors.accentBlue()} = props;

  const radixValue = Math.round(Math.max(0, Math.min(100, value)));
  const style = {
    '--progress-fill-color': fillColor,
    '--progress-value': radixValue,
  } as React.CSSProperties;

  return (
    <Progress.Root className={styles.root} style={style} value={radixValue} max={100}>
      <Progress.Indicator className={clsx(styles.indicator, animate && styles.animated)} />
    </Progress.Root>
  );
};
