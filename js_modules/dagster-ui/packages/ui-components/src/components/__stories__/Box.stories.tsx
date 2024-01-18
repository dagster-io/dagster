import * as React from 'react';
import {Meta} from '@storybook/react';
import styled from 'styled-components';

import {
  colorAccentBlue,
  colorAccentCyan,
  colorAccentGreen,
  colorAccentRed,
  colorAccentYellow,
  colorBackgroundGray,
} from '../../theme/color';
import {Box} from '../Box';
import {Group} from '../Group';
import {
  AlignItems,
  BorderSide,
  BorderWidth,
  FlexDirection,
  JustifyContent as JustifyContentType,
  Spacing,
} from '../types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Box',
  component: Box,
} as Meta;

export const Padding = () => {
  const spacings: Spacing[] = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64];
  return (
    <Group spacing={2} direction="row">
      {spacings.map((spacing) => (
        <Box key={`${spacing}`} background={colorBackgroundGray()} padding={spacing}>
          {spacing}
        </Box>
      ))}
    </Group>
  );
};

export const BorderSides = () => {
  const sides: BorderSide[] = [
    'all',
    'top-and-bottom',
    'left-and-right',
    'top',
    'right',
    'bottom',
    'left',
  ];
  const widths: BorderWidth[] = [1, 2];
  return (
    <Group direction="column" spacing={16}>
      {widths.map((width) => (
        <Group spacing={8} direction="column" key={`width-${width}`}>
          <div>{`Width ${width}:`}</div>
          <Group spacing={8} direction="row">
            {sides.map((side) => (
              <Box
                key={side}
                background={colorBackgroundGray()}
                border={{side, width, color: colorAccentBlue()}}
                padding={24}
                style={{fontSize: '12px', textTransform: 'uppercase'}}
              >
                {side}
              </Box>
            ))}
          </Group>
        </Group>
      ))}
    </Group>
  );
};

export const FlexDirections = () => {
  const directions: FlexDirection[] = ['row', 'column', 'row-reverse', 'column-reverse'];
  const alignItems: AlignItems[] = ['stretch', 'center', 'flex-start', 'flex-end'];

  return (
    <Group direction="column" spacing={16}>
      <div>Flex direction:</div>
      <Group spacing={24} direction="row">
        {directions.map((direction) => (
          <Group key={direction} direction="column" spacing={12}>
            <ExampleText>{direction}</ExampleText>
            <Box background={colorBackgroundGray()} flex={{direction}} padding={8}>
              <Box padding={12} background={colorAccentBlue()} />
              <Box padding={12} background={colorAccentCyan()} />
              <Box padding={12} background={colorAccentGreen()} />
              <Box padding={12} background={colorAccentYellow()} />
              <Box padding={12} background={colorAccentRed()} />
            </Box>
          </Group>
        ))}
      </Group>
      <div>Align items:</div>
      <Group spacing={24} direction="row">
        {alignItems.map((alignment) => (
          <Group key={alignment} direction="column" spacing={12}>
            <ExampleText>{alignment}</ExampleText>
            <Box
              background={colorBackgroundGray()}
              flex={{direction: 'row', alignItems: alignment}}
              padding={8}
            >
              <Box padding={12} background={colorAccentBlue()} />
              <Box padding={24} background={colorAccentCyan()} />
              <Box padding={32} background={colorAccentGreen()} />
              <Box padding={4} background={colorAccentYellow()} />
              <Box padding={16} background={colorAccentRed()} />
            </Box>
          </Group>
        ))}
      </Group>
    </Group>
  );
};

export const JustifyContent = () => {
  const justifyContent: JustifyContentType[] = [
    'space-between',
    'space-around',
    'space-evenly',
    'center',
    'flex-start',
    'flex-end',
  ];

  return (
    <Group direction="column" spacing={16}>
      <div>Justify content:</div>
      <Group spacing={24} direction="column">
        {justifyContent.map((option) => (
          <Group key={option} direction="column" spacing={12}>
            <ExampleText>{option}</ExampleText>
            <Box
              background={colorBackgroundGray()}
              flex={{direction: 'row', justifyContent: option}}
              padding={8}
            >
              <Box padding={12} background={colorAccentBlue()} />
              <Box padding={12} background={colorAccentCyan()} />
              <Box padding={12} background={colorAccentGreen()} />
              <Box padding={12} background={colorAccentYellow()} />
              <Box padding={12} background={colorAccentRed()} />
            </Box>
          </Group>
        ))}
      </Group>
    </Group>
  );
};

const ExampleText = styled.span`
  font-size: 12px;
  text-transform: uppercase;
`;
