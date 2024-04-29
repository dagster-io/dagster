import {QueryResult} from '@apollo/client';
import {renderHook} from '@testing-library/react-hooks';
import {ReactNode, useContext} from 'react';

import {
  CompletionType,
  Dependency,
  OrphanDependenciesTraceContext,
  TraceContext,
  useBlockTraceOnQueryResult,
  useDependency,
} from '../TraceContext';

describe('TraceContext', () => {
  it('provides default functions that do not throw', () => {
    const {result} = renderHook(() => useContext(TraceContext));
    expect(() => result.current.createDependency('test')).not.toThrow();
    expect(() => result.current.addDependency(null)).not.toThrow();
    expect(() => result.current.completeDependency(null, CompletionType.SUCCESS)).not.toThrow();
  });
});

describe('useBlockTraceOnQueryResult', () => {
  it('handles complete and error actions based on query data presence', () => {
    const mockAddDependency = jest.fn();
    const mockCompleteDependency = jest.fn();
    const context = {
      createDependency: () => new Dependency('test'),
      addDependency: mockAddDependency,
      completeDependency: mockCompleteDependency,
    };
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider value={context}>{children}</TraceContext.Provider>
    );

    const {rerender} = renderHook(
      ({queryResult}: {queryResult: QueryResult<any>}) =>
        useBlockTraceOnQueryResult(queryResult, 'testDep'),
      {initialProps: {queryResult: {data: null, error: null}}, wrapper} as any,
    );

    rerender({queryResult: {data: {}}} as any);
    expect(mockCompleteDependency).toHaveBeenCalledTimes(1);
    expect(mockCompleteDependency).toHaveBeenCalledWith(
      expect.any(Dependency),
      CompletionType.SUCCESS,
    );

    rerender({queryResult: {data: null, error: {}} as any});
    expect(mockCompleteDependency).toHaveBeenCalledTimes(2);
    expect(mockCompleteDependency).toHaveBeenCalledWith(
      expect.any(Dependency),
      CompletionType.ERROR,
    );
  });
});

describe('useDependency', () => {
  it('adds, completes, and cancels dependencies correctly', () => {
    const mockAddDependency = jest.fn();
    const mockCompleteDependency = jest.fn();
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider
        value={{
          createDependency: () => new Dependency('test'),
          addDependency: mockAddDependency,
          completeDependency: mockCompleteDependency,
        }}
      >
        {children}
      </TraceContext.Provider>
    );

    const {unmount} = renderHook(() => useDependency('testDep'), {wrapper});

    expect(mockAddDependency).toHaveBeenCalledTimes(1);
    unmount();
    expect(mockCompleteDependency).toHaveBeenCalledTimes(1);
    expect(mockCompleteDependency).toHaveBeenCalledWith(
      expect.any(Dependency),
      CompletionType.CANCELLED,
    );
  });
});

describe('OrphanDependenciesTraceContext', () => {
  it('ignores dependencies added within an orphaned tree', () => {
    const mockAddDependency = jest.fn();
    const mockCompleteDependency = jest.fn();
    const context = {
      createDependency: () => new Dependency('test'),
      addDependency: mockAddDependency,
      completeDependency: mockCompleteDependency,
    };
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider value={context}>
        <OrphanDependenciesTraceContext>{children}</OrphanDependenciesTraceContext>
      </TraceContext.Provider>
    );

    const {unmount} = renderHook(() => useDependency('testDep'), {wrapper});
    unmount();
    expect(mockAddDependency).not.toHaveBeenCalled();
    expect(mockCompleteDependency).not.toHaveBeenCalled();
  });
});
