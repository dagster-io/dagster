import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {Group} from './Group';
import {
  Suggestion,
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
} from './TokenizingField';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TokenizingField',
  component: TokenizingField,
} as Meta;

export const Default = () => {
  const [value, setValue] = React.useState<TokenizingFieldValue[]>([]);

  const suggestions = [
    {
      token: 'pipeline',
      values: () => ['airline_demo_ingest', 'airline_demo_warehouse', 'composition'],
    },
    {
      token: 'status',
      values: () => ['QUEUED', 'NOT_STARTED', 'STARTED', 'SUCCESS', 'FAILURE', 'MANAGED'],
    },
  ];

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={suggestions}
    />
  );
};

export const TokenProvider = () => {
  const [value, setValue] = React.useState<TokenizingFieldValue[]>([]);

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={[
        {values: () => ['ben@elementl.com', 'dish@elementl.com', 'marco@elementl.com']},
      ]}
    />
  );
};

export const TokenAndSuggestionProviders = () => {
  const [value, setValue] = React.useState<TokenizingFieldValue[]>([]);

  const users = {
    'ben@elementl.com': 'Ben Pankow',
    'dish@elementl.com': 'Isaac Hellendag',
    'marco@elementl.com': 'Marco Salazar',
  };
  const suggestions: SuggestionProvider[] = [
    {
      token: 'group',
      values: () => ['core@elementl.com', 'cloud@elementl.com'],
    },
    {
      values: () => Object.keys(users),
      suggestionFilter: (typed: string, s: Suggestion) =>
        s.text.toLowerCase().includes(typed.toLowerCase()) ||
        users[s.text].toLowerCase().includes(typed.toLowerCase()),
    },
  ];

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={suggestions}
    />
  );
};

export const CustomSuggestionRenderer = () => {
  const [value, setValue] = React.useState<TokenizingFieldValue[]>([]);
  const colors = {
    Red: Colors.Red500,
    Green: Colors.Green500,
    Blue: Colors.Blue500,
    Yellow: Colors.Yellow500,
  };

  const suggestionProviders: SuggestionProvider[] = [{values: () => Object.keys(colors)}];

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={suggestionProviders}
      suggestionRenderer={(suggestion) => (
        <Group direction="row" spacing={8} alignItems="center">
          <ColorSwatch $color={colors[suggestion.text]} />
          {suggestion.text}
        </Group>
      )}
    />
  );
};

const ColorSwatch = styled.div<{$color: string}>`
  border-radius: 50%;
  background-color: ${(p) => p.$color};
  width: 16px;
  height: 16px;
  border: 1px solid;
`;
