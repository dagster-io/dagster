// eslint-disable-next-line no-restricted-imports
import {Spinner as BlueprintSpinner} from '@blueprintjs/core';
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

  const style = fillColor ? ({'--spinner-fill-color': fillColor} as CSSProperties) : undefined;

  return (
    <div className={className} title={title} style={style}>
      <BlueprintSpinner
        className={styles.slowSpinner}
        value={value}
        size={SPINNER_SIZES[purpose]}
      />
    </div>
  );
};
