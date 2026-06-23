import {useState} from 'react';

import {Box} from '../Box';
import {Colors} from '../Color';
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

  const users: Record<string, string> = {
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
        !!users[s.text]?.toLowerCase().includes(typed.toLowerCase()),
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
        <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
          <ColorSwatch color={suggestion.text} />
          {suggestion.text}
        </Box>
      )}
    />
  );
};

const ColorSwatch = ({color}: {color: string}) => (
  <div
    style={{
      borderRadius: '50%',
      backgroundColor: color,
      width: 16,
      height: 16,
      border: '1px solid',
    }}
  />
);
