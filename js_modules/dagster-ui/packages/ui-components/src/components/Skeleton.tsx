import React from 'react';

import {Colors} from './Color';
import styles from './Skeleton.module.css';

type Props = {
  $height?: string | number;
  $width?: string | number;
  style?: React.CSSProperties;
};

export const Skeleton = ({$height, $width, style}: Props) => {
  const allStyles = {
    height: Number($height) ? `${$height}px` : ($height ?? '100%'),
    width: Number($width) ? `${$width}px` : ($width ?? '100%'),
    '--skeleton-bg': Colors.backgroundLight(),
    '--skeleton-bg-hover': Colors.backgroundLightHover(),
    ...style,
  } as React.CSSProperties;

  return <div className={styles.skeleton} style={allStyles} />;
};
