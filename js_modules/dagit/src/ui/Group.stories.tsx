import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Body, Code} from 'src/ui/Text';
import {AlignItems, Spacing} from 'src/ui/types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Group',
  component: Group,
} as Meta;

export const Horizontal = () => {
  const spacings: Spacing[] = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64];
  return (
    <Group spacing={12} direction="vertical">
      {spacings.map((spacing) => (
        <Box background={Colors.LIGHT_GRAY4} padding={8} key={`${spacing}`}>
          <Group direction="horizontal" spacing={spacing}>
            <ExampleText>
              <strong>{spacing}</strong>
            </ExampleText>
            <ExampleText>China</ExampleText>
            <ExampleText>France</ExampleText>
            <ExampleText>Russia</ExampleText>
            <ExampleText>United Kingdom</ExampleText>
            <ExampleText>United States</ExampleText>
          </Group>
        </Box>
      ))}
    </Group>
  );
};

export const Vertical = () => {
  const spacings: Spacing[] = [4, 8, 12, 16, 32, 48, 64];
  return (
    <Group spacing={12} direction="vertical">
      {spacings.map((spacing) => (
        <Box background={Colors.LIGHT_GRAY4} padding={12} key={`${spacing}`}>
          <Group direction="vertical" spacing={spacing}>
            <ExampleText>
              <strong>{spacing}</strong>
            </ExampleText>
            <ExampleText>China</ExampleText>
            <ExampleText>France</ExampleText>
            <ExampleText>Russia</ExampleText>
            <ExampleText>United Kingdom</ExampleText>
            <ExampleText>United States</ExampleText>
          </Group>
        </Box>
      ))}
    </Group>
  );
};

export const AlignItemsVertical = () => {
  const alignments: AlignItems[] = ['center', 'flex-start', 'flex-end'];
  return (
    <Group spacing={12} direction="vertical">
      {alignments.map((alignment) => (
        <Box background={Colors.LIGHT_GRAY4} padding={12} key={alignment}>
          <Group direction="vertical" alignItems={alignment} spacing={8}>
            <ExampleText>
              <strong>{alignment}</strong>
            </ExampleText>
            <ExampleText>France</ExampleText>
            <ExampleText>Russia</ExampleText>
            <ExampleText>United Kingdom</ExampleText>
            <ExampleText>United States</ExampleText>
          </Group>
        </Box>
      ))}
    </Group>
  );
};

export const EmptyChildren = () => {
  const EmptyThing = () => {
    return null;
  };

  return (
    <Group direction="vertical" spacing={12}>
      <Body>
        In the group below, two children are empty: one inline <Code>null</Code>, and one component
        that renders to <Code>null</Code>. Upon inspection of the DOM, note that both are given{' '}
        <Code>display: none</Code>.
      </Body>
      <Group background={Colors.LIGHT_GRAY5} padding={12} direction="vertical" spacing={8}>
        <ExampleText>China</ExampleText>
        <ExampleText>France</ExampleText>
        {null}
        <EmptyThing />
        <ExampleText>Russia</ExampleText>
        <ExampleText>United Kingdom</ExampleText>
        <ExampleText>United States</ExampleText>
      </Group>
    </Group>
  );
};

const ExampleText = styled.span`
  font-size: 12px;
  text-transform: uppercase;
`;
