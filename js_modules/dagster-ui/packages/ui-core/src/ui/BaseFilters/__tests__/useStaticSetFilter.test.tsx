import {IconName} from '@dagster-io/ui-components';
import {render, screen} from '@testing-library/react';
import {act, renderHook} from '@testing-library/react-hooks';
import {useState} from 'react';

import {useStaticSetFilter} from '../useStaticSetFilter';

describe('useStaticSetFilter', () => {
  const allValues = [
    {value: 'apple', match: ['apple']},
    {value: 'banana', match: ['banana']},
    {value: 'cherry', match: ['cherry']},
  ];

  function useTestHook(props: Partial<Parameters<typeof useStaticSetFilter<string>>[0]> = {}) {
    const [state, setState] = useState<Set<string>>(() => new Set(['banana']));

    return useStaticSetFilter<string>({
      name: 'Test',
      icon: 'asset' as IconName,
      allValues,
      renderLabel: ({value, isActive}: {value: string; isActive: boolean}) => (
        <span className={isActive ? 'active' : 'inactive'}>{value}</span>
      ),
      getStringValue: (value: string) => value,
      state,
      onStateChanged: setState,
      ...props,
    });
  }

  function createTestFilter() {
    return renderHook(() => useTestHook());
  }

  it('creates filter object with the correct properties', () => {
    const filter = renderHook(() => useTestHook());

    expect(filter.result.current).toHaveProperty('name', 'Test');
    expect(filter.result.current).toHaveProperty('icon', 'asset');
    expect(filter.result.current).toHaveProperty('state', new Set(['banana']));
  });

  function select(filter: ReturnType<typeof createTestFilter>, value: string) {
    const close = jest.fn();
    const createPortal = jest.fn();
    act(() => {
      filter.result.current.onSelect({
        value,
        close,
        createPortal,
        clearSearch: jest.fn(),
      });
    });
    return {close, createPortal};
  }

  it('adds and removes values from the state', () => {
    const filter = renderHook(() => useTestHook());
    const {close} = select(filter, 'apple');
    expect(filter.result.current.state).toEqual(new Set(['banana', 'apple']));
    expect(close.mock.calls.length).toEqual(0);

    select(filter, 'banana');
    expect(filter.result.current.state).toEqual(new Set(['apple']));
  });

  it('renders results with proper isActive state', () => {
    const filter = renderHook(() => useTestHook());
    const results = filter.result.current.getResults('');
    const {getByText} = render(
      <>
        {results.map((r) => (
          <span
            key={r.key}
            onClick={() => {
              select(filter, r.value);
            }}
          >
            {r.label}
          </span>
        ))}
      </>,
    );

    const apple = getByText('apple');
    const banana = getByText('banana');
    const cherry = getByText('cherry');

    expect(apple).not.toHaveClass('active');
    expect(banana).toHaveClass('active');
    expect(cherry).not.toHaveClass('active');
  });

  it('does not render "Select all" if allowMultipleSelections is false', async () => {
    const filter = renderHook(() =>
      useTestHook({
        allowMultipleSelections: false,
      }),
    );
    const results = filter.result.current.getResults('a');
    const {getByText, queryByText} = render(
      <>
        {results.map((r) => (
          <span key={r.key}>{r.label}</span>
        ))}
      </>,
    );

    const apple = getByText('apple');
    const banana = getByText('banana');
    const cherry = queryByText('cherry');
    const selectAll = queryByText('Select all');

    expect(apple).toBeVisible();
    expect(banana).toBeVisible();
    expect(cherry).not.toBeInTheDocument();
    expect(selectAll).not.toBeInTheDocument();
  });

  it('renders filtered results based on query and select all takes the query into account', async () => {
    const filter = renderHook(() => useTestHook());
    const results = filter.result.current.getResults('a');
    const {getByText, queryByText} = render(
      <>
        {results.map((r) => (
          <span key={r.key}>{r.label}</span>
        ))}
      </>,
    );

    const apple = getByText('apple');
    const banana = getByText('banana');
    const cherry = queryByText('cherry');
    const selectAll = screen.getByText('Select all');

    expect(apple).toBeVisible();
    expect(banana).toBeVisible();
    expect(cherry).not.toBeInTheDocument();

    expect(filter.result.current.state).toEqual(new Set(['banana']));

    expect(selectAll).toBeVisible();

    select(filter, Symbol.for('useStaticSetFilter:SelectAll') as any);

    expect(filter.result.current.state).toEqual(new Set(['banana', 'apple']));

    select(filter, Symbol.for('useStaticSetFilter:SelectAll') as any);

    expect(filter.result.current.state).toEqual(new Set([]));

    select(filter, 'cherry');

    expect(filter.result.current.state).toEqual(new Set(['cherry']));

    select(filter, Symbol.for('useStaticSetFilter:SelectAll') as any);

    expect(filter.result.current.state).toEqual(new Set(['cherry', 'banana', 'apple']));

    select(filter, Symbol.for('useStaticSetFilter:SelectAll') as any);

    expect(filter.result.current.state).toEqual(new Set(['cherry']));
  });

  it('reflects initial state', async () => {
    const props = {} as any;
    const filter = renderHook(() => useTestHook(props));
    select(filter, 'apple');
    expect(filter.result.current.state).toEqual(new Set(['banana', 'apple']));

    select(filter, 'banana');
    expect(filter.result.current.state).toEqual(new Set(['apple']));

    props.state = ['cherry'];

    filter.rerender();

    expect(filter.result.current.state).toEqual(new Set(['cherry']));
  });

  it('uses getKey to generate keys', () => {
    const filter = renderHook(() => useTestHook({getKey: (value: string) => value.toUpperCase()}));
    const results = filter.result.current.getResults('');
    results.forEach((result) => {
      if (typeof result.value === 'symbol') {
        // ignore the "select all symbol"
        return;
      }
      expect(result.key).toEqual(result.value.toUpperCase());
    });
  });
});
