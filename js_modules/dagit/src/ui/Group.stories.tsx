import {Colors} from '@blueprintjs/core';
import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components';

import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Body, Code, Heading, Subheading} from 'src/ui/Text';
import {AlignItems, Spacing} from 'src/ui/types';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Group',
  component: Group,
} as Meta;

export const Row = () => {
  const spacings: Spacing[] = [0, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64];
  return (
    <Group spacing={12} direction="column">
      {spacings.map((spacing) => (
        <Box background={Colors.LIGHT_GRAY4} padding={8} key={`${spacing}`}>
          <Group direction="row" spacing={spacing}>
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

export const Column = () => {
  const spacings: Spacing[] = [4, 8, 12, 16, 32, 48, 64];
  return (
    <Group spacing={12} direction="column">
      {spacings.map((spacing) => (
        <Box background={Colors.LIGHT_GRAY4} padding={12} key={`${spacing}`}>
          <Group direction="column" spacing={spacing}>
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

export const AlignItemsColumn = () => {
  const alignments: AlignItems[] = ['center', 'flex-start', 'flex-end'];
  return (
    <Group spacing={12} direction="column">
      {alignments.map((alignment) => (
        <Box background={Colors.LIGHT_GRAY4} padding={12} key={alignment}>
          <Group direction="column" alignItems={alignment} spacing={8}>
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
    <Group direction="column" spacing={12}>
      <Body>
        In the group below, two children are empty: one inline <Code>null</Code>, and one component
        that renders to <Code>null</Code>. Upon inspection of the DOM, note that both are given{' '}
        <Code>display: none</Code>.
      </Body>
      <Group background={Colors.LIGHT_GRAY5} padding={12} direction="column" spacing={8}>
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

export const PointerEventsTest = () => {
  return (
    <div>
      <ButtonLink
        color={{link: Colors.BLUE3, hover: Colors.ORANGE3}}
        onClick={() => console.log('Clicked!')}
      >
        <strong>Try to click me!</strong>
      </ButtonLink>
      <Group direction="column" spacing={32}>
        <Group direction="column" spacing={32}>
          <Heading>Heading</Heading>
          <div style={{width: '500px'}}>
            This is a Group within a Group, which results in overlapping negative margins. We want
            to be sure that the user can still interact with elements that are overlapped by the
            relevant margins.
          </div>
        </Group>
        <Subheading>Subheading</Subheading>
      </Group>
    </div>
  );
};

const ExampleText = styled.span`
  font-size: 12px;
  text-transform: uppercase;
`;
