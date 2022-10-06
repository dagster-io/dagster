import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {useSuggestionsForString} from './useSuggestionsForString';

describe('useSuggestionsForString', () => {
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

  const buildSuggestions = (queryString: string): string[] =>
    queryString
      ? values.filter((value) => value.toLowerCase().startsWith(queryString))
      : [...empties];

  const Test = () => {
    const [value, setValue] = React.useState('');
    const {suggestions, onSelectSuggestion} = useSuggestionsForString(buildSuggestions, value);

    return (
      <>
        <input type="text" value={value} onChange={(e) => setValue(e.target.value)} />
        <ul>
          {suggestions.map((suggestion) => (
            <li key={suggestion} onClick={() => setValue(onSelectSuggestion(suggestion))}>
              {suggestion}
            </li>
          ))}
        </ul>
      </>
    );
  };

  it('determines suggestions for empty string', () => {
    render(<Test />);
    expect(screen.getByText('query:')).toBeVisible();
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('state:')).toBeVisible();
  });

  it('determines suggestions for query', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), 'pr');
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('prez:washington')).toBeVisible();
    expect(screen.getByText('prez:adams')).toBeVisible();
    expect(screen.getByText('prez:jefferson')).toBeVisible();
  });

  it('determines suggestions when querystring matches a suggestion exactly', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), 'prez:');
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('prez:washington')).toBeVisible();
    expect(screen.getByText('prez:adams')).toBeVisible();
    expect(screen.getByText('prez:jefferson')).toBeVisible();
  });

  it('determines suggestions only for the last segment of the string', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), 'query pr');
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('prez:washington')).toBeVisible();
    expect(screen.queryByText('query:')).toBeNull();
  });

  it('trims the input string when determining suggestions', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), '     pr     ');
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('prez:washington')).toBeVisible();
  });

  it('replaces the last segment with the suggestion, if selected', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), 'pre');
    expect(screen.getByText('prez:')).toBeVisible();
    expect(screen.getByText('prez:washington')).toBeVisible();
  });

  it('replaces only the last segment with the suggestion', () => {
    render(<Test />);
    await userEvent.type(screen.getByRole('textbox'), 'query pre');
    const prez = screen.getByText('prez:');
    userEvent.click(prez);
    const input = screen.getByRole('textbox');
    expect(input).toHaveValue('query prez:');
  });
});
