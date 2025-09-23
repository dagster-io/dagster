import {useState} from 'react';
import styled from 'styled-components';

import {Colors} from '../Color';
import {Group} from '../Group';
import {
  Suggestion,
  SuggestionProvider,
  TokenizingField,
  TokenizingFieldValue,
} from '../TokenizingField';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'TokenizingField',
  component: TokenizingField,
};

export const Default = () => {
  const [value, setValue] = useState<TokenizingFieldValue[]>([]);

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
  const [value, setValue] = useState<TokenizingFieldValue[]>([]);

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={[
        {values: () => ['ben@dagsterlabs.com', 'dish@dagsterlabs.com', 'marco@dagsterlabs.com']},
      ]}
    />
  );
};

export const TokenAndSuggestionProviders = () => {
  const [value, setValue] = useState<TokenizingFieldValue[]>([]);

  const users = {
    'ben@dagsterlabs.com': 'Ben Pankow',
    'dish@dagsterlabs.com': 'Isaac Hellendag',
    'marco@dagsterlabs.com': 'Marco Salazar',
  };
  const suggestions: SuggestionProvider[] = [
    {
      token: 'group',
      values: () => ['core@dagsterlabs.com', 'cloud@dagsterlabs.com'],
    },
    {
      values: () => Object.keys(users),
      suggestionFilter: (typed: string, s: Suggestion) =>
        s.text.toLowerCase().includes(typed.toLowerCase()) ||
        (users as any)[s.text].toLowerCase().includes(typed.toLowerCase()),
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
  const [value, setValue] = useState<TokenizingFieldValue[]>([]);
  const colors = {
    Red: Colors.accentRed(),
    Green: Colors.accentGreen(),
    Blue: Colors.accentBlue(),
    Yellow: Colors.accentYellow(),
  };

  const suggestionProviders: SuggestionProvider[] = [{values: () => Object.keys(colors)}];

  return (
    <TokenizingField
      values={value}
      onChange={(values) => setValue(values)}
      suggestionProviders={suggestionProviders}
      suggestionRenderer={(suggestion) => (
        <Group direction="row" spacing={8} alignItems="center">
          <ColorSwatch $color={suggestion.text} />
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
