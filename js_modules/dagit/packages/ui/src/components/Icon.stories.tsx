import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {Box} from './Box';
import {ColorsWIP} from './Colors';
import {IconNames, IconWIP as Icon} from './Icon';
import {Tooltip} from './Tooltip';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Icon',
  component: Icon,
} as Meta;

export const Size16 = () => {
  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} />
        </Tooltip>
      ))}
    </Box>
  );
};

export const Size24 = () => {
  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} size={24} />
        </Tooltip>
      ))}
    </Box>
  );
};

export const IconColors = () => {
  const colorKeys = Object.keys(ColorsWIP);
  const numColors = colorKeys.length;
  const colorAtIndex = (index: number) => {
    const colorKey = colorKeys[index % numColors];
    if (colorKey) {
      const colorAtKey = ColorsWIP[colorKey];
      if (colorAtKey) {
        return colorAtKey;
      }
    }
    return ColorsWIP.Gray100;
  };

  return (
    <Box flex={{gap: 6, wrap: 'wrap'}}>
      {IconNames.map((name, idx) => (
        <Tooltip content={name} key={name}>
          <Icon name={name} color={colorAtIndex(idx)} size={24} />
        </Tooltip>
      ))}
    </Box>
  );
};
