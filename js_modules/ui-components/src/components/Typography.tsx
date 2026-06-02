import clsx from 'clsx';
import * as React from 'react';

import {Colors} from './Color';
import styles from './css/Typography.module.css';

type FontSize = 12 | 14 | 16 | 18 | 20 | 24 | 32;
type FontWeight = 400 | 500 | 600;
type FontFamily = 'default' | 'mono';
type ThemeColor = keyof typeof Colors;

const getSizeClass = (size: FontSize) => {
  switch (size) {
    case 12:
      return styles.size12;
    case 14:
      return styles.size14;
    case 16:
      return styles.size16;
    case 18:
      return styles.size18;
    case 20:
      return styles.size20;
    case 24:
      return styles.size24;
    case 32:
      return styles.size32;
    default:
      throw new Error(`Unsupported font size: '${size satisfies never}'`);
  }
};

const getWeightClass = (weight: FontWeight) => {
  switch (weight) {
    case 400:
      return styles.weight400;
    case 500:
      return styles.weight500;
    case 600:
      return styles.weight600;
    default:
      throw new Error(`Unsupported font weight: '${weight satisfies never}'`);
  }
};

type HeadingProps = Omit<React.HTMLAttributes<HTMLElement>, 'color'> & {
  size: FontSize;
  weight: Exclude<FontWeight, 400>;
  family?: FontFamily;
  color?: ThemeColor;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'span';
};

export const Heading = ({
  size,
  weight,
  family = 'default',
  color,
  as: Component = 'span',
  className,
  style,
  ...props
}: HeadingProps) => (
  <Component
    {...props}
    className={clsx(
      getSizeClass(size),
      getWeightClass(weight),
      family === 'mono' && styles.familyMono,
      styles.trackingTight,
      className,
    )}
    style={color ? {...style, color: Colors[color]()} : style}
  />
);

type TextProps = Omit<React.HTMLAttributes<HTMLElement>, 'color'> & {
  size: FontSize;
  weight?: FontWeight;
  family?: FontFamily;
  color?: ThemeColor;
  as?: 'p' | 'div' | 'span';
};

export const Text = ({
  size,
  weight = 400,
  family = 'default',
  color,
  as: Component = 'span',
  className,
  style,
  ...props
}: TextProps) => (
  <Component
    {...props}
    className={clsx(
      getSizeClass(size),
      getWeightClass(weight),
      family === 'mono' && styles.familyMono,
      className,
    )}
    style={color ? {...style, color: Colors[color]()} : style}
  />
);
