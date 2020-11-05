import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {AlignItems, BorderSide, FlexDirection, Spacing} from 'src/ui/types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Box',
  component: Box,
} as Meta;

export const Padding = () => {
  const spacings: Spacing[] = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64];
  return (
    <Group spacing={2} direction="horizontal">
      {spacings.map((spacing) => (
        <Box key={`${spacing}`} background={Colors.LIGHT_GRAY2} padding={spacing}>
          {spacing}
        </Box>
      ))}
    </Group>
  );
};

export const BorderSides = () => {
  const sides: BorderSide[] = ['all', 'horizontal', 'vertical', 'top', 'right', 'bottom', 'left'];
  return (
    <Group direction="vertical" spacing={16}>
      <div>Light color:</div>
      <Group spacing={8} direction="horizontal">
        {sides.map((side) => (
          <Box
            key={side}
            background={Colors.LIGHT_GRAY5}
            border={{side, width: 1, color: 'light'}}
            padding={24}
            style={{fontSize: '12px', textTransform: 'uppercase'}}
          >
            {side}
          </Box>
        ))}
      </Group>
      <div>Medium color:</div>
      <Group spacing={8} direction="horizontal">
        {sides.map((side) => (
          <Box
            key={side}
            background={Colors.LIGHT_GRAY5}
            border={{side, width: 1, color: 'medium'}}
            padding={24}
            style={{fontSize: '12px', textTransform: 'uppercase'}}
          >
            {side}
          </Box>
        ))}
      </Group>
      <div>Dark color:</div>
      <Group spacing={8} direction="horizontal">
        {sides.map((side) => (
          <Box
            key={side}
            background={Colors.LIGHT_GRAY5}
            border={{side, width: 1, color: 'dark'}}
            padding={24}
            style={{fontSize: '12px', textTransform: 'uppercase'}}
          >
            {side}
          </Box>
        ))}
      </Group>
    </Group>
  );
};

export const FlexDirections = () => {
  const directions: FlexDirection[] = ['row', 'column', 'row-reverse', 'column-reverse'];
  const alignItems: AlignItems[] = ['stretch', 'center', 'flex-start', 'flex-end'];

  return (
    <Group direction="vertical" spacing={16}>
      <div>Flex direction:</div>
      <Group spacing={24} direction="horizontal">
        {directions.map((direction) => (
          <Group key={direction} direction="vertical" spacing={12}>
            <ExampleText>{direction}</ExampleText>
            <Box background={Colors.LIGHT_GRAY5} flex={{direction}} padding={8}>
              <Box padding={12} background={Colors.BLUE1} />
              <Box padding={12} background={Colors.BLUE2} />
              <Box padding={12} background={Colors.BLUE3} />
              <Box padding={12} background={Colors.BLUE4} />
              <Box padding={12} background={Colors.BLUE5} />
            </Box>
          </Group>
        ))}
      </Group>
      <div>Align items:</div>
      <Group spacing={24} direction="horizontal">
        {alignItems.map((alignment) => (
          <Group key={alignment} direction="vertical" spacing={12}>
            <ExampleText>{alignment}</ExampleText>
            <Box
              background={Colors.LIGHT_GRAY5}
              flex={{direction: 'row', alignItems: alignment}}
              padding={8}
            >
              <Box padding={12} background={Colors.BLUE1} />
              <Box padding={24} background={Colors.BLUE2} />
              <Box padding={32} background={Colors.BLUE3} />
              <Box padding={4} background={Colors.BLUE4} />
              <Box padding={16} background={Colors.BLUE5} />
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
