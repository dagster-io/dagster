import clsx from 'clsx';
import React from 'react';

import styles from './css/RunMatrixUtils.module.css';

export const BOX_SIZE = 32;

const TITLE_MARGIN_BOTTOM = 15;

export function topLabelHeightForLabels(labels: string[]) {
  let maxLength = 0;
  for (const label of labels) {
    maxLength = Math.max(maxLength, label.length);
  }
  return (maxLength > 10 ? maxLength * 4.9 : 55) + TITLE_MARGIN_BOTTOM;
}

export const GridColumn = ({
  disabled,
  hovered,
  focused,
  multiselectFocused,
  className,
  ...rest
}: {
  disabled?: boolean;
  hovered?: boolean;
  focused?: boolean;
  multiselectFocused?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={clsx(
      styles.gridColumn,
      disabled && styles.disabled,
      focused && styles.focused,
      multiselectFocused && styles.multiselectFocused,
      hovered && styles.hovered,
      !disabled && !focused && !multiselectFocused && !hovered && styles.hoverable,
      className,
    )}
    {...rest}
  />
);

export const LeftLabel = ({
  hovered,
  className,
  ...rest
}: {hovered?: boolean} & React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.leftLabel, hovered && styles.hovered, className)} {...rest} />
);

export const TopLabel = ({className, ...rest}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.topLabel, className)} {...rest} />
);

export const TopLabelTilted = ({label, $height}: {label: string; $height: number}) => {
  return (
    <div className={styles.topLabelTiltedInner} style={{height: $height - TITLE_MARGIN_BOTTOM}}>
      <div className="tilted">{label}</div>
    </div>
  );
};

export const GRID_FLOATING_CONTAINER_WIDTH = 330;

export const GridFloatingContainer = ({
  floating,
  className,
  ...rest
}: {floating: boolean} & React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={clsx(styles.gridFloatingContainer, floating && styles.floating, className)}
    {...rest}
  />
);
