import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';

import {TokenizingField} from './TokenizingField';

describe('TokenizingField', () => {
  const onChange = jest.fn();
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
  const tokens = ['all_sensors'];

  const getItems = () => {
    const items = screen.getAllByRole('listitem');
    return items.map((item) => item.textContent);
  };

  it('shows available autocompletion options when clicked', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    expect(input).toBeVisible();
    userEvent.click(input);

    await waitFor(() => {
      expect(getItems()).toEqual(['pipeline:', 'status:']);
    });
  });

  it('shows available autocompletion options when clicked, with raw tokens', async () => {
    render(
      <TokenizingField
        values={[]}
        onChange={onChange}
        suggestionProviders={suggestions}
        tokens={tokens}
      />,
    );

    const input = screen.getByRole('textbox');
    expect(input).toBeVisible();
    userEvent.click(input);

    await waitFor(() => {
      expect(getItems()).toEqual(['all_sensors', 'pipeline:', 'status:']);
    });
  });

  it('filters properly when typing `pipeline` prefix', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    userEvent.click(input);
    userEvent.type(input, 'pipeli');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    userEvent.clear(input);
    userEvent.type(input, 'pipeline');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    userEvent.clear(input);
    userEvent.type(input, 'pipeline:');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });
  });

  it('filters properly when typing a value without the preceding token', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    userEvent.click(input);
    userEvent.type(input, 'airline');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
      ]);
    });
  });

  it('filters properly when typing a value with raw tokens', async () => {
    render(
      <TokenizingField
        values={[]}
        onChange={onChange}
        suggestionProviders={suggestions}
        tokens={tokens}
      />,
    );

    const input = screen.getByRole('textbox');
    userEvent.click(input);
    userEvent.type(input, 'all');

    await waitFor(() => {
      expect(getItems()).toEqual(['all_sensors']);
    });
  });
});
