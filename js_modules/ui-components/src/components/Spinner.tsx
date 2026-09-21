import clsx from 'clsx';
import {CSSProperties} from 'react';

import styles from './css/Spinner.module.css';

type SpinnerPurpose = 'page' | 'section' | 'body-text' | 'caption-text';

const SPINNER_SIZES: Record<SpinnerPurpose, number> = {
  page: 80,
  section: 32,
  'caption-text': 10,
  'body-text': 12,
};

const RADIUS = 45;
const PATH_LENGTH = 280;
const SPINNER_TRACK = `M 50,50 m 0,-${RADIUS} a ${RADIUS},${RADIUS} 0 1 1 0,${
  RADIUS * 2
} a ${RADIUS},${RADIUS} 0 1 1 0,-${RADIUS * 2}`;
const STROKE_WIDTH = 4;
const MIN_STROKE_WIDTH = 16;

interface Props {
  purpose: SpinnerPurpose;
  value?: number;
  fillColor?: string;
  stopped?: boolean;
  title?: string;
}

export const Spinner = ({purpose, value, fillColor, stopped, title = 'Loading…'}: Props) => {
  const className = clsx(
    'spinnerGlobal', // Global class for targeting spinners
    styles.spinner,
    stopped ? styles.stopped : null,
    purpose === 'caption-text' && styles.captionText,
    purpose === 'body-text' && styles.bodyText,
  );

  const size = SPINNER_SIZES[purpose];
  const strokeWidth = Math.min(MIN_STROKE_WIDTH, (STROKE_WIDTH * SPINNER_SIZES.page) / size);
  const radius = RADIUS + strokeWidth / 2;
  const viewBox = `${50 - radius} ${50 - radius} ${radius * 2} ${radius * 2}`;
  const clampedValue = value === undefined ? undefined : Math.max(0, Math.min(1, value));
  const strokeOffset = PATH_LENGTH - PATH_LENGTH * (clampedValue ?? 0.25);

  const style = fillColor ? ({'--spinner-fill-color': fillColor} as CSSProperties) : undefined;

  return (
    <div
      aria-label="loading"
      aria-valuemax={100}
      aria-valuemin={0}
      aria-valuenow={clampedValue === undefined ? undefined : clampedValue * 100}
      className={className}
      role="progressbar"
      title={title}
      style={style}
    >
      <svg width={size} height={size} strokeWidth={strokeWidth.toFixed(2)} viewBox={viewBox}>
        <path className={styles.track} d={SPINNER_TRACK} />
        <path
          className={styles.head}
          d={SPINNER_TRACK}
          pathLength={PATH_LENGTH}
          strokeDasharray={`${PATH_LENGTH} ${PATH_LENGTH}`}
          strokeDashoffset={strokeOffset}
        />
      </svg>
    </div>
  );
};
