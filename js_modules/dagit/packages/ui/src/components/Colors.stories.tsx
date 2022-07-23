// eslint-disable-next-line no-restricted-imports
import {Colors as BlueprintColors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import nearestColor from 'nearest-color';
import * as React from 'react';
import rgbHex from 'rgb-hex';

import {Box} from './Box';
import {Colors} from './Colors';

const ColorExample: React.FC<{name: string; color: string}> = ({color, name}) => (
  <Box background={color} padding={12} style={{width: 120}}>
    {name}
  </Box>
);

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Colors',
  component: ColorExample,
} as Meta;

const ColorsToHex = Object.keys(Colors).reduce(
  (accum, key) => ({...accum, [key]: `#${rgbHex(Colors[key]).slice(0, 6)}`}),
  {},
);

const toCurrent = nearestColor.from(ColorsToHex);

const BlueprintToHex = Object.keys(BlueprintColors).reduce(
  (accum, key) => ({...accum, [key]: `${BlueprintColors[key].slice(0, 7)}`}),
  {},
);

export const Comparison = () => {
  return (
    <Box flex={{direction: 'row', gap: 4}}>
      <Box flex={{direction: 'column', alignItems: 'stretch', gap: 4}}>
        <div>Current colors</div>
        {Object.keys(ColorsToHex).map((key) => (
          <ColorExample key={key} name={key} color={ColorsToHex[key]} />
        ))}
      </Box>
      <Box flex={{direction: 'column', alignItems: 'stretch', gap: 4}}>
        <div>Blueprint colors</div>
        {Object.keys(BlueprintToHex).map((key) => (
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}} key={key}>
            <ColorExample name={key} color={BlueprintToHex[key]} />
            <div>{toCurrent(BlueprintToHex[key]).name}</div>
          </Box>
        ))}
      </Box>
    </Box>
  );
};
