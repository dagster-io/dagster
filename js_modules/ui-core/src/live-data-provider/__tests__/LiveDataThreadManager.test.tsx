import {LiveDataThreadManager} from '../LiveDataThreadManager';

type Data = {value: number};

// The thread starts its fetch loop via a 50ms scheduler delay + requestAnimationFrame, and then
// re-checks for work every 5s. Advance past a tick so any eligible fetch has been issued and its
// promise settled.
const TICK_MS = 5100;

describe('LiveDataThreadManager', () => {
  let consoleError: jest.SpyInstance;

  beforeEach(() => {
    jest.useFakeTimers();
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleError.mockRestore();
    jest.useRealTimers();
  });

  it('refetches a key after a refresh fails with a non-500 error', async () => {
    const queryKeys = jest.fn<Promise<Record<string, Data>>, [string[]]>();
    const manager = new LiveDataThreadManager<Data>(queryKeys, 10, 1);
    manager.setPollRate(1000);

    const listener = jest.fn();

    // Initial fetch succeeds and populates the cache.
    queryKeys.mockResolvedValueOnce({a: {value: 1}});
    manager.subscribe('a', listener);
    await jest.advanceTimersByTimeAsync(200);
    expect(queryKeys).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenLastCalledWith('a', {value: 1});

    // The next refresh fails the way a dropped connection does (no HTTP status in the message).
    queryKeys.mockRejectedValueOnce(new Error('Failed to fetch'));
    await jest.advanceTimersByTimeAsync(TICK_MS);
    expect(queryKeys).toHaveBeenCalledTimes(2);

    // The key must be retried, not orphaned with its stale cached value.
    queryKeys.mockResolvedValueOnce({a: {value: 2}});
    await jest.advanceTimersByTimeAsync(TICK_MS);
    expect(queryKeys).toHaveBeenCalledTimes(3);
    expect(queryKeys.mock.calls[2]?.[0]).toEqual(['a']);
    expect(listener).toHaveBeenLastCalledWith('a', {value: 2});
    expect(manager.getCacheEntry('a')).toEqual({value: 2});
  });

  it('waits a full poll interval before retrying a key after a 500 error', async () => {
    const queryKeys = jest.fn<Promise<Record<string, Data>>, [string[]]>();
    const manager = new LiveDataThreadManager<Data>(queryKeys, 10, 1);
    manager.setPollRate(60_000);

    const listener = jest.fn();

    queryKeys.mockResolvedValueOnce({a: {value: 1}});
    manager.subscribe('a', listener);
    await jest.advanceTimersByTimeAsync(200);
    expect(queryKeys).toHaveBeenCalledTimes(1);

    // Make the key eligible for a refresh, then fail it with a backend 500.
    await jest.advanceTimersByTimeAsync(60_000);
    queryKeys.mockRejectedValueOnce(new Error('Response not successful: Received status code 500'));
    await jest.advanceTimersByTimeAsync(TICK_MS);
    expect(queryKeys).toHaveBeenCalledTimes(2);

    // A 500 is treated as "too expensive, back off": no retry until the poll interval elapses...
    await jest.advanceTimersByTimeAsync(TICK_MS * 2);
    expect(queryKeys).toHaveBeenCalledTimes(2);

    // ...after which the key is fetched again.
    queryKeys.mockResolvedValueOnce({a: {value: 2}});
    await jest.advanceTimersByTimeAsync(60_000);
    expect(queryKeys).toHaveBeenCalledTimes(3);
    expect(listener).toHaveBeenLastCalledWith('a', {value: 2});
  });
});
