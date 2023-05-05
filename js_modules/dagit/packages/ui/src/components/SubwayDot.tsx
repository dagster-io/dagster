// eslint-disable-next-line no-restricted-imports
import {Colors} from '@blueprintjs/core';
import memoize from 'lodash/memoize';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Icon, IconName} from './Icon';

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
  return colors[index]!;
});

type IconProps = React.ComponentProps<typeof Icon>;

export const SubwayDot: React.FC<{
  label: string;
  fontSize?: number;
  icon?: IconName;
  iconSize?: IconProps['size'];
  blobColor?: string;
  blobSize?: number;
}> = React.memo(({label, fontSize = 13, blobColor, icon, iconSize = 16, blobSize = 24}) => (
  <Blob $color={blobColor || colorForString(label)} $blobSize={blobSize} $fontSize={fontSize}>
    {icon ? (
      <Icon
        size={iconSize}
        name={icon}
        color={Colors.WHITE}
        style={{marginLeft: 0, marginTop: 0, opacity: 0.9}}
      />
    ) : (
      label.slice(0, 1)
    )}
  </Blob>
));

interface BlobProps {
  $color: string;
  $blobSize: number;
  $fontSize: number;
}

const Blob = styled.div<BlobProps>`
  align-items: center;
  background-color: ${({$color}) => $color};
  border-radius: 50%;
  color: ${Colors.WHITE};
  cursor: pointer;
  display: flex;
  flex-shrink: 0;
  font-size: ${({$fontSize}) => `${$fontSize}px`};
  height: ${({$blobSize}) => `${$blobSize}px`};
  justify-content: center;
  outline: none;
  text-transform: uppercase;
  transition: background 50ms linear, color 50ms linear;
  user-select: none;
  width: ${({$blobSize}) => `${$blobSize}px`};

  :focus,
  :active {
    outline: none;
  }
`;
