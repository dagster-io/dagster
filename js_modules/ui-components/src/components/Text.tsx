import clsx from 'clsx';
import * as React from 'react';

import styles from './css/Text.module.css';

interface TextProps extends React.HTMLAttributes<HTMLElement> {
  as?: React.ElementType;
  color?: string;
  htmlFor?: string;
  [key: string]: any;
}

const Text = ({as: Component = 'span', color, style, className, ...props}: TextProps) => (
  <Component className={className} style={color ? {...style, color} : style} {...props} />
);

export const Body = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.body, className)} {...props} />
);

export const Body1 = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.body1, className)} {...props} />
);

export const Body2 = ({className, ...props}: TextProps) => (
  <Text className={clsx('body2Global', styles.body2, className)} {...props} />
);

export const Caption = ({className, ...props}: TextProps) => (
  <Text className={clsx('captionGlobal', styles.caption, className)} {...props} />
);

export const CaptionSubtitle = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.captionSubtitle, className)} {...props} />
);

export const CaptionBolded = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.captionBolded, className)} {...props} />
);

export const BodyLarge = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.bodyLarge, className)} {...props} />
);

export const BodySmall = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.bodySmall, className)} {...props} />
);
