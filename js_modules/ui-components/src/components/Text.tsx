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

export const Title = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.title, className)} {...props} />
);

export const Heading = ({className, ...props}: TextProps) => (
  <Text className={clsx('headingGlobal', styles.heading, className)} {...props} />
);

export const Headline = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.headline, className)} {...props} />
);

export const Subheading = ({className, ...props}: TextProps) => (
  <Text className={clsx('subheadingGlobal', styles.subheading, className)} {...props} />
);

export const Subtitle1 = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.subtitle1, className)} {...props} />
);

export const Subtitle2 = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.subtitle2, className)} {...props} />
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

export const Code = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.code, className)} {...props} />
);

export const Mono = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.mono, className)} {...props} />
);

export const CaptionMono = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.captionMono, className)} {...props} />
);

export const SubtitleLarge = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.subtitleLarge, className)} {...props} />
);

export const Subtitle = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.subtitle, className)} {...props} />
);

export const SubtitleSmall = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.subtitleSmall, className)} {...props} />
);

export const BodyLarge = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.bodyLarge, className)} {...props} />
);

export const BodySmall = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.bodySmall, className)} {...props} />
);

export const MonoLarge = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.monoLarge, className)} {...props} />
);

export const MonoSmall = ({className, ...props}: TextProps) => (
  <Text className={clsx(styles.monoSmall, className)} {...props} />
);
