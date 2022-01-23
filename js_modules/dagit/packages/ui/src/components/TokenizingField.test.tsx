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

  const expectOptions = (expected: string[]) => {
    const items = screen.getAllByRole('listitem');
    const actual = items.map((item) => item.textContent);
    expect(actual).toEqual(expected);
  };

  it('shows available autocompletion options when clicked', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    expect(input).toBeVisible();
    userEvent.click(input);

    await waitFor(() => {
      expectOptions(['pipeline:', 'status:']);
    });
  });

  it('filters properly when typing `pipeline` prefix', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    userEvent.click(input);
    userEvent.type(input, 'pipeli');

    await waitFor(() => {
      expectOptions([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    userEvent.clear(input);
    userEvent.type(input, 'pipeline');

    await waitFor(() => {
      expectOptions([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    userEvent.clear(input);
    userEvent.type(input, 'pipeline:');

    await waitFor(() => {
      expectOptions([
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
      expectOptions(['pipeline:airline_demo_ingest', 'pipeline:airline_demo_warehouse']);
    });
  });
});
