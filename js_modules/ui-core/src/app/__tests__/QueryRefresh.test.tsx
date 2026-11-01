import {act, cleanup, fireEvent, render, renderHook, screen} from '@testing-library/react';

import {ApolloError, NetworkStatus} from '../../apollo-client';
import {__updateSearchVisibility} from '../../search/useSearchVisibility';
import {QueryRefreshCountdown, useRefreshAtInterval} from '../QueryRefresh';

describe('useRefreshAtInterval', () => {
  let consoleError: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    cleanup();
    __updateSearchVisibility(false);
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  it('repeats synchronous refreshes after the minimum loading time', async () => {
    const refresh = jest.fn();
    const {result} = renderHook(() => useRefreshAtInterval({refresh, intervalMs: 15000}));

    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(result.current).toMatchObject({loading: true});
    await act(() => jest.advanceTimersByTimeAsync(1000));
    expect(result.current).toMatchObject({loading: false});
    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).toHaveBeenCalledTimes(2);
  });

  it.each([false, true])(
    'retries after an automatic Apollo error (leading=%s)',
    async (leading) => {
      const error = new ApolloError({networkError: new Error('Offline')});
      const refresh = jest.fn().mockRejectedValueOnce(error).mockResolvedValue('ok');
      const {result} = renderHook(() =>
        useRefreshAtInterval({refresh, intervalMs: 15000, leading}),
      );

      if (!leading) {
        await act(() => jest.advanceTimersByTimeAsync(15000));
      }
      expect(refresh).toHaveBeenCalledTimes(1);
      await act(() => jest.advanceTimersByTimeAsync(1000));
      expect(result.current).toMatchObject({loading: false});

      await act(() => jest.advanceTimersByTimeAsync(15000));
      expect(refresh).toHaveBeenCalledTimes(2);
      expect(consoleError).not.toHaveBeenCalled();
    },
  );

  it('refreshes after global search closes', async () => {
    const error = new ApolloError({networkError: new Error('Offline')});
    const refresh = jest.fn().mockRejectedValueOnce(error).mockResolvedValue('ok');
    const {result} = renderHook(() => useRefreshAtInterval({refresh, intervalMs: 15000}));

    act(() => __updateSearchVisibility(true));
    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).not.toHaveBeenCalled();
    act(() => __updateSearchVisibility(false));
    expect(refresh).toHaveBeenCalledTimes(1);
    await act(() => jest.advanceTimersByTimeAsync(1000));
    expect(result.current).toMatchObject({loading: false});
    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).toHaveBeenCalledTimes(2);
  });

  it('refreshes after the document becomes visible', async () => {
    const visibilityState = jest
      .spyOn(document, 'visibilityState', 'get')
      .mockReturnValue('hidden');
    const error = new ApolloError({networkError: new Error('Offline')});
    const refresh = jest.fn().mockRejectedValueOnce(error).mockResolvedValue('ok');
    const {result} = renderHook(() => useRefreshAtInterval({refresh, intervalMs: 15000}));

    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).not.toHaveBeenCalled();

    act(() => {
      visibilityState.mockReturnValue('visible');
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(refresh).toHaveBeenCalledTimes(1);
    await act(() => jest.advanceTimersByTimeAsync(1000));
    expect(result.current).toMatchObject({loading: false});
    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).toHaveBeenCalledTimes(2);
  });

  it('preserves manual refresh errors while allowing the next refresh', async () => {
    const error = new Error('Offline');
    const refresh = jest.fn().mockRejectedValueOnce(error).mockResolvedValue('ok');
    const {result} = renderHook(() => useRefreshAtInterval({refresh, intervalMs: 15000}));
    let rejected: Promise<unknown> | undefined;

    act(() => {
      rejected = result.current.refetch().catch((caught) => caught);
    });
    await act(() => jest.advanceTimersByTimeAsync(1000));
    expect(await rejected).toBe(error);
    expect(result.current).toMatchObject({loading: false});

    await act(() => jest.advanceTimersByTimeAsync(15000));
    expect(refresh).toHaveBeenCalledTimes(2);
  });

  it('reports unexpected errors from automatic and countdown refreshes', async () => {
    const automaticError = new Error('Automatic failure');
    const automaticRefresh = jest.fn().mockRejectedValue(automaticError);
    renderHook(() => useRefreshAtInterval({refresh: automaticRefresh, intervalMs: 15000}));

    await act(() => jest.advanceTimersByTimeAsync(16000));
    expect(consoleError).toHaveBeenCalledWith('Unexpected error refreshing data', automaticError);

    const manualError = new Error('Manual failure');
    render(
      <QueryRefreshCountdown
        refreshState={{
          loading: false,
          nextFireMs: Date.now() + 15000,
          nextFireDelay: 15000,
          refetch: jest.fn().mockRejectedValue(manualError),
        }}
      />,
    );
    fireEvent.click(screen.getByRole('button'));
    await act(async () => {});
    expect(consoleError).toHaveBeenCalledWith('Unexpected error refreshing data', manualError);
  });

  it('reports Apollo errors that include client errors', async () => {
    const clientError = new Error('Client failure');
    const error = new ApolloError({
      networkError: new Error('Offline'),
      clientErrors: [clientError],
    });
    const refetch = jest.fn().mockRejectedValue(error);
    render(
      <QueryRefreshCountdown
        refreshState={{
          loading: false,
          nextFireMs: Date.now() + 15000,
          nextFireDelay: 15000,
          refetch,
        }}
      />,
    );

    fireEvent.click(screen.getByRole('button'));
    await act(async () => {});
    expect(consoleError).toHaveBeenCalledWith('Unexpected error refreshing data', error);
  });

  it('continues the countdown after a network error', async () => {
    render(
      <QueryRefreshCountdown
        refreshState={{
          networkStatus: NetworkStatus.error,
          nextFireMs: Date.now() + 15000,
          nextFireDelay: 15000,
          refetch: jest.fn(),
        }}
      />,
    );

    await act(() => jest.advanceTimersByTimeAsync(2000));
    expect(await screen.findByText('0:13')).toBeVisible();
  });
});
