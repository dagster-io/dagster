import clsx from 'clsx';
import * as React from 'react';
import {CSSProperties} from 'react';

import {Colors} from './Color';
import styles from './css/BaseTag.module.css';

export interface BaseTagProps {
  fillColor?: string;
  textColor?: string;
  icon?: React.ReactNode;
  interactive?: boolean;
  rightIcon?: React.ReactNode;
  label?: React.ReactNode;
  tooltipText?: string;
  children?: React.ReactNode;
  className?: string;
}

const BaseTagTooltipStyle: React.CSSProperties = {
  fontSize: 12,
  lineHeight: '16px',
  alignItems: 'center',
  padding: '4px 8px',
  userSelect: 'text',
  pointerEvents: 'none',
  borderRadius: 8,
  border: 'none',
  top: -9,
  left: -13,
};

export const BaseTag = (props: BaseTagProps) => {
  const {
    fillColor = Colors.backgroundDefault(),
    textColor = Colors.textDefault(),
    icon,
    interactive = false,
    rightIcon,
    label,
    tooltipText,
    children,
    className,
  } = props;

  const tagStyle: CSSProperties = {
    '--tag-fill-color': fillColor,
    '--tag-text-color': textColor,
  } as CSSProperties;

  return (
    <div
      className={clsx('BaseTag', styles.baseTag, interactive && styles.interactive, className)}
      style={tagStyle}
    >
      {children ?? (
        <>
          {icon || null}
          {label !== undefined && label !== null ? (
            <span
              data-tooltip={typeof label === 'string' ? label : tooltipText}
              data-tooltip-style={JSON.stringify({
                ...BaseTagTooltipStyle,
                backgroundColor: Colors.tooltipBackground(),
                color: Colors.tooltipText(),
              })}
            >
              {label}
            </span>
          ) : null}
          {rightIcon || null}
        </>
      )}
    </div>
  );
};
