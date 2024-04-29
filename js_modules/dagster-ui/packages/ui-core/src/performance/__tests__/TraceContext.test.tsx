import {renderHook} from '@testing-library/react-hooks';
import {ReactNode, useContext} from 'react';

import {
  Dependency,
  OrphanedTraceContext,
  TraceContext,
  useDependency,
  useQueryResultDependency,
} from '../TraceContext';

describe('TraceContext', () => {
  it('provides default functions that do not throw', () => {
    const {result} = renderHook(() => useContext(TraceContext));
    expect(() => result.current.createDependency({name: 'test'})).not.toThrow();
    expect(() => result.current.addDependency(null)).not.toThrow();
    expect(() => result.current.cancelDependency(null)).not.toThrow();
    expect(() => result.current.completeDependency(null)).not.toThrow();
  });
});

describe('useQueryResultDependency', () => {
  it('handles complete and cancel actions based on query data presence', () => {
    const mockAddDependency = jest.fn();
    const mockCompleteDependency = jest.fn();
    const mockCancelDependency = jest.fn();
    const context = {
      createDependency: () => new Dependency({name: 'test'}),
      addDependency: mockAddDependency,
      cancelDependency: mockCancelDependency,
      completeDependency: mockCompleteDependency,
    };
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider value={context}>{children}</TraceContext.Provider>
    );

    const {rerender, unmount} = renderHook(
      ({queryResult}: any) => useQueryResultDependency(queryResult as any, 'testDep'),
      {initialProps: {queryResult: {data: null}} as any, wrapper},
    );

    rerender({queryResult: {data: {}}} as any);

    expect(mockCompleteDependency).toHaveBeenCalledTimes(1);

    unmount();

    expect(mockCancelDependency).toHaveBeenCalledTimes(1);
  });
});

describe('useDependency', () => {
  it('adds and cancels dependencies correctly', () => {
    const mockAddDependency = jest.fn();
    const mockCancelDependency = jest.fn();
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider
        value={{
          createDependency: () => new Dependency({name: 'test'}),
          addDependency: mockAddDependency,
          cancelDependency: mockCancelDependency,
          completeDependency: jest.fn(),
        }}
      >
        {children}
      </TraceContext.Provider>
    );

    const {unmount} = renderHook(() => useDependency({name: 'testDep'}), {wrapper});

    expect(mockAddDependency).toHaveBeenCalledTimes(1);
    unmount();
    expect(mockCancelDependency).toHaveBeenCalledTimes(1);
  });
});

describe('OrphanedTraceContext', () => {
  it('ignores dependencies added within an oprhaned tree', () => {
    const mockAddDependency = jest.fn();
    const mockCompleteDependency = jest.fn();
    const mockCancelDependency = jest.fn();
    const context = {
      createDependency: () => new Dependency({name: 'test'}),
      addDependency: mockAddDependency,
      cancelDependency: mockCancelDependency,
      completeDependency: mockCompleteDependency,
    };
    const wrapper = ({children}: {children: ReactNode}) => (
      <TraceContext.Provider value={context}>
        <OrphanedTraceContext>{children}</OrphanedTraceContext>
      </TraceContext.Provider>
    );

    const {unmount} = renderHook(
      ({queryResult}: any) => useQueryResultDependency(queryResult as any, 'testDep'),
      {initialProps: {queryResult: {data: null}} as any, wrapper},
    );
    unmount();
    expect(mockAddDependency).not.toHaveBeenCalled();
    expect(mockCancelDependency).not.toHaveBeenCalled();
    expect(mockCompleteDependency).not.toHaveBeenCalled();
  });
});
