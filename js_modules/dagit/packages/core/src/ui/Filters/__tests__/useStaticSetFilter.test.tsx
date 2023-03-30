import {render} from '@testing-library/react';
import {act, renderHook} from '@testing-library/react-hooks';
import React from 'react';

import {useStaticSetFilter} from '../useStaticSetFilter';

describe('useStaticSetFilter', () => {
  const allValues = [
    {value: 'apple', match: ['apple']},
    {value: 'banana', match: ['banana']},
    {value: 'cherry', match: ['cherry']},
  ];

  function createTestFilter() {
    return renderHook(() =>
      useStaticSetFilter({
        name: 'Test',
        icon: 'asset',
        allValues,
        renderLabel: ({value, isActive}) => (
          <span className={isActive ? 'active' : 'inactive'}>{value}</span>
        ),
        getStringValue: (value: string) => value,
        initialState: ['banana'],
      }),
    );
  }

  it('creates filter object with the correct properties', () => {
    const filter = createTestFilter();

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
      });
    });
    return {close, createPortal};
  }

  it('adds and removes values from the state', () => {
    const filter = createTestFilter();
    const {close} = select(filter, 'apple');
    expect(filter.result.current.state).toEqual(new Set(['banana', 'apple']));
    expect(close.mock.calls.length).toEqual(0);

    select(filter, 'banana');
    expect(filter.result.current.state).toEqual(new Set(['apple']));
  });

  it('renders results with proper isActive state', () => {
    const filter = createTestFilter();
    const results = filter.result.current.getResults('');
    const {getByText} = render(
      <>
        {results.map((r) => (
          <span
            key={r.key}
            onClick={() => {
              console.log('onClick', r.value);
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

  it('renders filtered results based on query', () => {
    const filter = createTestFilter();
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

    expect(apple).toBeInTheDocument();
    expect(banana).toBeInTheDocument();
    expect(cherry).not.toBeInTheDocument();
  });
});
