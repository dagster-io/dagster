import {Meta} from '@storybook/react/types-6-0';
import * as React from 'react';

import {ButtonLink} from './ButtonLink';
import {Colors} from './Colors';
import {Group} from './Group';
import {useSuggestionsForString} from './useSuggestionsForString';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'useSuggestionsForString',
} as Meta;

const empties = ['query:', 'prez:', 'state:'];

const values = [
  ...empties,
  'prez:washington',
  'prez:adams',
  'prez:jefferson',
  'state:hull',
  'state:rusk',
  'state:shultz',
];

export const Example = () => {
  const [value, setValue] = React.useState('');
  const buildSuggestions = React.useCallback(
    (queryString: string): string[] =>
      queryString
        ? values.filter((value) => value.toLowerCase().startsWith(queryString))
        : [...empties],
    [],
  );

  const {suggestions, onSelectSuggestion} = useSuggestionsForString(buildSuggestions, value);

  const onChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => setValue(e.target.value),
    [setValue],
  );

  return (
    <Group direction="column" spacing={12}>
      <input
        type="text"
        value={value}
        onChange={onChange}
        style={{
          border: `1px solid ${Colors.Gray400}`,
          borderRadius: '3px',
          padding: '8px',
          fontSize: '14px',
          width: '500px',
        }}
      />
      <div>
        {suggestions.map((suggestion) => (
          <div key={suggestion}>
            <ButtonLink
              onMouseDown={(e: React.MouseEvent<any>) => {
                e.preventDefault();
                setValue(onSelectSuggestion(suggestion));
              }}
            >
              {suggestion}
            </ButtonLink>
          </div>
        ))}
      </div>
    </Group>
  );
};
