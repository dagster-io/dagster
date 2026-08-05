import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import {SuggestionProvider, TokenizingField} from '../TokenizingField';

// useVirtualizer needs a scrollable container with real dimensions in JSDOM.
beforeAll(() => {
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    get: () => 235,
  });
  Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
    configurable: true,
    get: () => 400,
  });

  class MockResizeObserver {
    callback: ResizeObserverCallback;
    targets: Element[] = [];
    constructor(callback: ResizeObserverCallback) {
      this.callback = callback;
    }
    observe(target: Element) {
      this.targets.push(target);
      this.callback(
        [
          {
            target,
            contentRect: {width: 400, height: 235, top: 0, left: 0, bottom: 235, right: 400},
            borderBoxSize: [{blockSize: 235, inlineSize: 400}],
            contentBoxSize: [{blockSize: 235, inlineSize: 400}],
            devicePixelContentBoxSize: [{blockSize: 235, inlineSize: 400}],
          } as unknown as ResizeObserverEntry,
        ],
        this as unknown as ResizeObserver,
      );
    }
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
});

describe('TokenizingField', () => {
  const onChange = jest.fn();
  const suggestions: SuggestionProvider[] = [
    {
      token: 'pipeline',
      values: () => ['airline_demo_ingest', 'airline_demo_warehouse', 'composition'],
    },
    {
      token: 'status',
      values: () => ['QUEUED', 'NOT_STARTED', 'STARTED', 'SUCCESS', 'FAILURE', 'MANAGED'],
    },
  ];
  const suggestionsWithTokens: SuggestionProvider[] = [
    ...suggestions,
    {values: () => ['all_sensors', 'some_sensors']},
  ];
  const suggestionsWithCustomMatchLogic: SuggestionProvider[] = [
    ...suggestions,
    {
      values: () => ['all_sensors', 'all'],
      suggestionFilter: (q, s) => s.text === q,
    },
  ];

  const getItems = () => {
    const items = screen.getAllByRole('menuitem');
    return items.map((item) => item.textContent);
  };

  it('shows available autocompletion options when clicked', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    expect(input).toBeVisible();
    await userEvent.click(input);

    await waitFor(() => {
      expect(getItems()).toEqual(['pipeline:', 'status:']);
    });
  });

  it('shows available autocompletion options when clicked, with raw tokens', async () => {
    render(
      <TokenizingField
        values={[]}
        onChange={onChange}
        suggestionProviders={suggestionsWithTokens}
      />,
    );

    const input = screen.getByRole('textbox');
    expect(input).toBeVisible();
    await userEvent.click(input);

    await waitFor(() => {
      expect(getItems()).toEqual(['all_sensors', 'pipeline:', 'some_sensors', 'status:']);
    });
  });

  it('filters properly when typing `pipeline` prefix', async () => {
    render(<TokenizingField values={[]} onChange={onChange} suggestionProviders={suggestions} />);

    const input = screen.getByRole('textbox');
    await userEvent.click(input);
    await userEvent.type(input, 'pipeli');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    await userEvent.clear(input);
    await userEvent.type(input, 'pipeline');

    await waitFor(() => {
      expect(getItems()).toEqual([
        'pipeline:',
        'pipeline:airline_demo_ingest',
        'pipeline:airline_demo_warehouse',
        'pipeline:composition',
      ]);
    });

    await userEvent.clear(input);
    await userEvent.type(input, 'pipeline:');

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
    await userEvent.click(input);
    await userEvent.type(input, 'airline');

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
        suggestionProviders={suggestionsWithTokens}
      />,
    );

    const input = screen.getByRole('textbox');
    await userEvent.click(input);
    await userEvent.type(input, 'aLl');

    await waitFor(() => {
      expect(getItems()).toEqual(['all_sensors']);
    });
  });

  it('test custom filter logic', async () => {
    render(
      <TokenizingField
        values={[]}
        onChange={onChange}
        suggestionProviders={suggestionsWithCustomMatchLogic}
      />,
    );

    const input = screen.getByRole('textbox');
    await userEvent.click(input);
    await userEvent.type(input, 'ALL');

    await waitFor(() => {
      expect(getItems()).toEqual(['all']);
    });
  });
});
