import {CSSProperties} from 'react';

import styles from './css/PezItem.module.css';

const MIN_OPACITY = 0.2;
const MAX_OPACITY = 1.0;
const MIN_OPACITY_STEPS = 3;

interface Props {
  color: string;
  opacity: number;
}

export const PezItem = ({color, opacity}: Props) => {
  return (
    <div
      className={styles.pezItem}
      style={{'--pez-color': color, '--pez-opacity': opacity} as CSSProperties}
    />
  );
};

export const calculatePezOpacity = (index: number, total: number) => {
  const countForStep = Math.max(MIN_OPACITY_STEPS, total);
  const step = (MAX_OPACITY - MIN_OPACITY) / countForStep;
  return MAX_OPACITY - (total - index - 1) * step;
};
