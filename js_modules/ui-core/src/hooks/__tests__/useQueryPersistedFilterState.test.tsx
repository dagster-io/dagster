import {act, renderHook} from '@testing-library/react-hooks';
import React from 'react';
import {MemoryRouter} from 'react-router';

import {useQueryPersistedFilterState} from '../useQueryPersistedFilterState';

const wrapper = ({
  initialEntries,
}: {
  initialEntries?: React.ComponentProps<typeof MemoryRouter>['initialEntries'];
} = {}) => {
  return ({children}: {children: React.ReactNode}) => (
    <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
  );
};

describe('useQueryPersistedFilterState', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with decoded state from query string', () => {
    const {result} = renderHook(
      () =>
        useQueryPersistedFilterState<{filterA: string[]; filterB: string[]}>([
          'filterA',
          'filterB',
        ]),
      {
        wrapper: wrapper({
          initialEntries: [
            `/?filterA=${encodeURIComponent(
              JSON.stringify(['value1']),
            )}&filterB=${encodeURIComponent(JSON.stringify(['value2']))}`,
          ],
        }),
      },
    );

    expect(result.current.state).toEqual({
      filterA: ['value1'],
      filterB: ['value2'],
    });
  });

  it('should encode the state correctly when setting a value', () => {
    const {result} = renderHook(
      () =>
        useQueryPersistedFilterState<{filterA: string[]; filterB: string[]}>([
          'filterA',
          'filterB',
        ]),
      {wrapper: wrapper()},
    );

    act(() => {
      result.current.setters.setFilterA(['newValue']);
    });

    expect(result.current.state.filterA).toEqual(['newValue']);
  });

  it('should create setters dynamically for each filter field', () => {
    const {result} = renderHook(
      () =>
        useQueryPersistedFilterState<{filterA: string[]; filterB: string[]}>([
          'filterA',
          'filterB',
        ]),
      {wrapper: wrapper()},
    );

    expect(result.current.setters).toHaveProperty('setFilterA');
    expect(result.current.setters).toHaveProperty('setFilterB');

    act(() => {
      result.current.setters.setFilterA(['valueA']);
      result.current.setters.setFilterB(['valueB']);
    });

    expect(result.current.state.filterA).toEqual(['valueA']);
    expect(result.current.state.filterB).toEqual(['valueB']);
  });

  it('should handle undefined or empty values correctly', () => {
    const {result} = renderHook(
      () =>
        useQueryPersistedFilterState<{
          filterA: string[] | undefined;
          filterB: string[] | undefined;
        }>(['filterA', 'filterB']),
      {wrapper: wrapper()},
    );

    act(() => {
      result.current.setters.setFilterA([]);
      result.current.setters.setFilterB(undefined);
    });

    expect(result.current.state.filterA).toEqual([]);
    expect(result.current.state.filterB).toEqual([]);
  });

  it('should return memoized setters', () => {
    const FIELDS = ['filterA', 'filterB'] as const;
    const {result, rerender} = renderHook(
      () => useQueryPersistedFilterState<{filterA: string[]; filterB: string[]}>(FIELDS),
      {wrapper: wrapper()},
    );

    const initialSetters = result.current.setters;

    rerender();

    expect(result.current.setters).toBe(initialSetters);
  });
});
