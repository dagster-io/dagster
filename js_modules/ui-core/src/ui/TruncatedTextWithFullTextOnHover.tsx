import {Colors} from '@dagster-io/ui-components';
import * as React from 'react';

import styles from './css/TruncatedTextWithFullTextOnHover.module.css';

export const LabelTooltipStyles = JSON.stringify({
  background: Colors.backgroundLight(),
  filter: `brightness(97%)`,
  color: Colors.textDefault(),
  border: 'none',
  borderRadius: 7,
  overflow: 'hidden',
  fontSize: 14,
  padding: '5px 10px',
  transform: 'translate(-10px,-5px)',
} as React.CSSProperties);

export const TruncatedTextWithFullTextOnHover = React.forwardRef(
  (
    {
      text,
      tooltipStyle,
      tooltipText,
      ...rest
    }:
      | {text: string; tooltipStyle?: string; tooltipText?: null}
      | {text: React.ReactNode; tooltipStyle?: string; tooltipText: string},
    ref: React.ForwardedRef<HTMLDivElement>,
  ) => (
    <div
      className={styles.truncatingName}
      data-tooltip={tooltipText ?? text}
      data-tooltip-style={tooltipStyle ?? LabelTooltipStyles}
      ref={ref}
      {...rest}
    >
      {text}
    </div>
  ),
);
