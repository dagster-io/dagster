import {renderHook, act} from '@testing-library/react-hooks';
import React from 'react';

import {useSuggestionFilter} from '../useSuggestionFilter';

describe('useSuggestionFilter', () => {
  const initialSuggestions = [
    {value: 'apple'},
    {value: 'banana'},
    {value: 'cherry'},
    {value: 'date'},
  ];

  const getStringValue = (value: string) => value;
  const getKey = (value: string) => value;
  const renderLabel = ({value, isActive}: {value: string; isActive: boolean}) => (
    <div>{isActive ? `*${value}*` : value}</div>
  );
  const isMatch = (value: string, query: string) => value.startsWith(query);

  const asyncSuggestions = [
    {final: true, value: 'pear'},
    {final: true, value: 'peach'},
  ];

  const onSuggestionClicked = async (value: string) => {
    if (value === 'p') {
      return asyncSuggestions;
    }
    return [];
  };

  const hookArgs = {
    name: 'test',
    icon: 'job' as const,
    initialSuggestions,
    onSuggestionClicked,
    getStringValue,
    getKey,
    renderLabel,
    isMatch,
  };

  it('should have correct initial state', () => {
    const {result} = renderHook(() =>
      useSuggestionFilter({...hookArgs, state: [], setState: () => {}}),
    );

    expect(result.current.state).toEqual([]);
    expect(result.current.isActive).toBe(false);
  });

  it('should handle active and inactive states', () => {
    let state: string[] = [];
    const {result, rerender} = renderHook(() =>
      useSuggestionFilter({...hookArgs, state, setState: () => {}}),
    );
    expect(result.current.isActive).toBe(false);

    state = ['apple'];
    rerender();

    expect(result.current.isActive).toBe(true);
  });

  it('should select and deselect suggestions', async () => {
    let state: string[] = [];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const {result, rerender} = renderHook(() =>
      useSuggestionFilter({...hookArgs, state, setState}),
    );

    expect(result.current.state).toEqual([]);

    await act(async () => {
      await result.current.onSelect({value: {final: true, value: 'apple'}} as any);
    });
    rerender();

    expect(result.current.state).toEqual(['apple']);

    await act(async () => {
      await result.current.onSelect({value: {final: true, value: 'apple'}} as any);
    });
    rerender();

    expect(result.current.state).toEqual([]);
  });

  it('should load and display next suggestions', async () => {
    let state: string[] = [];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const {result} = renderHook(() => useSuggestionFilter({...hookArgs, state, setState}));

    expect(result.current.getResults('p')).toEqual([]);

    const clearSearchFn = jest.fn();
    await act(async () => {
      result.current.onSelect({
        value: {final: false, value: 'p'},
        clearSearch: clearSearchFn,
        createPortal: () => () => {},
        close: () => {},
      });
    });
    expect(clearSearchFn).toHaveBeenCalled();

    const expectedResult = asyncSuggestions.filter(({value}) => isMatch(value, 'p'));

    expect(result.current.getResults('p').map((suggestion) => suggestion.value)).toEqual(
      expectedResult,
    );
  });

  it('should filter suggestions based on a query', () => {
    let state: string[] = [];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const {result} = renderHook(() => useSuggestionFilter({...hookArgs, state, setState}));

    const expectedResult = initialSuggestions.filter(({value}) => isMatch(value, 'a'));

    expect(result.current.getResults('a').map((suggestion) => suggestion.value)).toEqual(
      expectedResult,
    );
  });

  it('should handle empty initialSuggestions', () => {
    const {result} = renderHook(() =>
      useSuggestionFilter({...hookArgs, initialSuggestions: [], state: [], setState: () => {}}),
    );

    expect(result.current.getResults('')).toEqual([]);
  });

  it('should handle empty query', () => {
    let state: string[] = [];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const {result} = renderHook(() => useSuggestionFilter({...hookArgs, state, setState}));

    expect(result.current.getResults('').map((suggestion) => suggestion.value)).toEqual(
      initialSuggestions,
    );
  });

  it('should handle freeformSearchResult', async () => {
    let state: string[] = [];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const freeformSearchResult = (query: string) => ({final: true, value: `Custom: ${query}`});
    const {result} = renderHook(() =>
      useSuggestionFilter({...hookArgs, freeformSearchResult, state, setState}),
    );

    const expectedResult = [
      {final: true, value: 'Custom: test'},
      ...initialSuggestions.filter(({value}) => isMatch(value, 'test')),
    ];

    expect(result.current.getResults('test').map((suggestion) => suggestion.value)).toEqual(
      expectedResult,
    );
  });

  it('should handle renderActiveStateLabel', () => {
    let state: string[] = ['apple'];
    const setState = (newState: string[]) => {
      state = newState;
    };

    const renderActiveStateLabel = ({value, isActive}: {value: string; isActive: boolean}) => (
      <div>{isActive ? `(${value})` : value}</div>
    );
    const {result} = renderHook(() =>
      useSuggestionFilter({...hookArgs, renderActiveStateLabel, state, setState}),
    );

    expect(result.current.activeJSX).toBeTruthy();
  });
});
