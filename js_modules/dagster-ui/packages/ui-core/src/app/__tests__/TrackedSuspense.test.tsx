import {act, render, waitFor} from '@testing-library/react';

import {TrackedSuspense, TrackedSuspenseProvider} from '../TrackedSuspense';

describe('TrackedSuspenseProvider', () => {
  it('manages boundaries correctly', async () => {
    const mockContentRendered = jest.fn();
    const mockContentRemoved = jest.fn();
    const mockFallbackRendered = jest.fn();
    const mockFallbackRemoved = jest.fn();

    const state = {
      promises: {} as Record<string, Promise<any>>,
      resolvers: {} as Record<string, (value: any) => void>,
      resolved: {} as Record<string, boolean>,
    };

    function Suspender({id}: {id: string}) {
      if (!state.promises[id]) {
        state.promises[id] = new Promise((res) => {
          state.resolvers[id] = (value: any) => {
            state.resolved[id] = true;
            res(value);
          };
        });
      }
      if (!state.resolved[id]) {
        throw state.promises[id];
      }
      return id;
    }

    render(
      <TrackedSuspenseProvider
        onContentRendered={mockContentRendered}
        onContentRemoved={mockContentRemoved}
        onFallbackRendered={mockFallbackRendered}
        onFallbackRemoved={mockFallbackRemoved}
      >
        <TrackedSuspense id="test1" fallback={<div>Loading 1...</div>}>
          <TrackedSuspense id="test2" fallback={<div>Loading 2...</div>}>
            <Suspender id="test2" />
          </TrackedSuspense>
          <TrackedSuspense id="test3" fallback={<div>Loading 3...</div>}>
            <Suspender id="test3" />
          </TrackedSuspense>
        </TrackedSuspense>
        <TrackedSuspense id="test4" fallback={<div>Loading 4...</div>}>
          <Suspender id="test4" />
        </TrackedSuspense>
      </TrackedSuspenseProvider>,
    );

    // test1 is rendered since it doesn't suspend
    expect(mockContentRendered).toHaveBeenCalledTimes(1);
    expect(mockContentRendered).toHaveBeenNthCalledWith(1, {
      id: 'test1',
    });

    expect(mockFallbackRendered).toHaveBeenCalledTimes(3);

    expect(mockFallbackRendered).toHaveBeenNthCalledWith(1, {
      id: 'test2',
    });
    expect(mockFallbackRendered).toHaveBeenNthCalledWith(2, {
      id: 'test3',
    });
    expect(mockFallbackRendered).toHaveBeenNthCalledWith(3, {
      id: 'test4',
    });
    expect(mockFallbackRemoved).toHaveBeenCalledTimes(0);
    act(() => {
      state.resolvers['test2']!(1);
    });
    await waitFor(() => {
      expect(mockFallbackRemoved).toHaveBeenCalledTimes(1);
      expect(mockContentRendered).toHaveBeenCalledTimes(2);
      expect(mockContentRendered).toHaveBeenNthCalledWith(2, {
        id: 'test2',
      });
    });
    act(() => {
      state.resolvers['test3']!(1);
    });
    await waitFor(() => {
      expect(mockFallbackRemoved).toHaveBeenCalledTimes(2);
      expect(mockContentRendered).toHaveBeenCalledTimes(3);
      expect(mockContentRendered).toHaveBeenNthCalledWith(3, {
        id: 'test3',
      });
    });
    act(() => {
      state.resolvers['test4']!(1);
    });
    await waitFor(() => {
      expect(mockFallbackRemoved).toHaveBeenCalledTimes(3);
      expect(mockContentRendered).toHaveBeenCalledTimes(4);
      expect(mockContentRendered).toHaveBeenNthCalledWith(4, {
        id: 'test4',
      });
    });
  });
});
