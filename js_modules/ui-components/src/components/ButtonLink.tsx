import clsx from 'clsx';
import {CSSProperties} from 'react';

import {Colors} from './Color';
import styles from './css/ButtonLink.module.css';

type Colors =
  | string
  | {
      link: string;
      hover?: string;
      active?: string;
    };

type Underline = 'never' | 'always' | 'hover';

const getColorVars = (color: Colors) => {
  const values = typeof color === 'string' ? {link: color, hover: color, active: color} : color;
  return {
    '--button-link-color': values.link,
    '--button-link-hover-color': values.hover,
    '--button-link-active-color': values.active,
  } as CSSProperties;
};

const getTextDecorationClassName = (underline: Underline) => {
  return clsx(
    underline === 'always' && styles.textDecorationAlways,
    underline === 'hover' && styles.textDecorationHover,
  );
};

interface Props extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'color'> {
  color?: Colors;
  underline?: Underline;
}

export const ButtonLink = ({
  color,
  underline,
  style: userStyle,
  className: userClassName,
  ...rest
}: Props) => {
  const colors = color ? getColorVars(color) : {};
  const textDecoration = underline ? getTextDecorationClassName(underline) : undefined;
  const style = {
    ...userStyle,
    ...colors,
  };

  return (
    <button
      {...rest}
      style={style}
      className={clsx(styles.buttonLink, textDecoration, userClassName)}
    />
  );
};
