import memoize from 'lodash/memoize';
import * as React from 'react';
import {CSSProperties} from 'react';

import {Colors} from './Color';
import {Icon, IconName} from './Icon';
import styles from './css/SubwayDot.module.css';

const SECONDARY_COLORS = {
  Orchid: '#8982DD',
  Fern: '#508E74',
  Teal: '#0080B6',
  Rose: '#D16FA4',
  Ruby: '#CF4C49',
  Gold: '#CC8430',
  Stone: '#8F988C',
  Sand: '#9E7D56',
  Mustard: '#BDB247',
};

const colors = [
  SECONDARY_COLORS.Orchid,
  SECONDARY_COLORS.Fern,
  SECONDARY_COLORS.Teal,
  SECONDARY_COLORS.Rose,
  SECONDARY_COLORS.Ruby,
  SECONDARY_COLORS.Gold,
  SECONDARY_COLORS.Stone,
  SECONDARY_COLORS.Sand,
  SECONDARY_COLORS.Mustard,
];

const colorForString = memoize((s: string) => {
  const index =
    Math.abs(
      s.split('').reduce((a, b) => {
        a = (a << 5) - a + b.charCodeAt(0);
        return a & a;
      }, 0),
    ) % colors.length;
  return colors[index] ?? '';
});

type IconProps = React.ComponentProps<typeof Icon>;

interface Props {
  label: string;
  fontSize?: number;
  icon?: IconName;
  iconSize?: IconProps['size'];
  blobColor?: string;
  blobSize?: number;
}

export const SubwayDot = React.memo(
  ({label, fontSize = 13, blobColor, icon, iconSize = 16, blobSize = 24}: Props) => {
    const style: CSSProperties = {
      '--blob-color': blobColor || colorForString(label),
      '--blob-size': `${blobSize}px`,
      '--blob-font-size': `${fontSize}px`,
    } as CSSProperties;

    return (
      <div className={styles.blob} style={style}>
        {icon ? (
          <Icon
            size={iconSize}
            name={icon}
            color={Colors.accentReversed()}
            style={{marginLeft: 0, marginTop: 0, opacity: 0.9}}
          />
        ) : (
          label.slice(0, 1)
        )}
      </div>
    );
  },
);
