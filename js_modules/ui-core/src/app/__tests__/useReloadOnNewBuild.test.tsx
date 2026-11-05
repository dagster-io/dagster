import {renderHook} from '@testing-library/react';

import {
  requestRefreshEverywhere,
  useReloadOnNewBuild,
  useReloadOnRemoteRefresh,
} from '../useReloadOnNewBuild';

const page = (bundle: string) =>
  `<!DOCTYPE html><html><head><script src="/static/${bundle}.js"></script></head><body></body></html>`;

const flush = async () => {
  for (let i = 0; i < 5; i++) {
    await Promise.resolve();
  }
};

describe('useReloadOnNewBuild', () => {
  const reload = jest.fn();
  let served: string;

  beforeEach(() => {
    jest.useFakeTimers();
    reload.mockReset();
    window.sessionStorage.clear();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {pathname: '/hillpointe', reload},
    });
    served = page('main.aaa');
    global.fetch = jest.fn(async () => ({ok: true, text: async () => served})) as any;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('reloads once when the served bundles change, and not before', async () => {
    renderHook(() => useReloadOnNewBuild());
    await flush();
    expect(reload).not.toHaveBeenCalled();

    jest.advanceTimersByTime(5 * 60 * 1000);
    await flush();
    expect(reload).not.toHaveBeenCalled();

    served = page('main.bbb');
    jest.advanceTimersByTime(5 * 60 * 1000);
    await flush();
    expect(reload).toHaveBeenCalledTimes(1);

    // The same new build seen again (e.g. a cached HTML) must not loop.
    jest.advanceTimersByTime(5 * 60 * 1000);
    await flush();
    expect(reload).toHaveBeenCalledTimes(1);
  });
});

describe('useReloadOnRemoteRefresh', () => {
  const reload = jest.fn();
  let at: number;

  beforeEach(() => {
    jest.useFakeTimers();
    reload.mockReset();
    window.sessionStorage.clear();
    Object.defineProperty(window, 'location', {configurable: true, value: {reload}});
    at = 1000;
    global.fetch = jest.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        at += 1;
      }
      return {ok: true, json: async () => ({at})};
    }) as any;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('reloads when another page requests a refresh, and not before', async () => {
    renderHook(() => useReloadOnRemoteRefresh());
    await flush();
    jest.advanceTimersByTime(30 * 1000);
    await flush();
    expect(reload).not.toHaveBeenCalled();

    at += 1;
    jest.advanceTimersByTime(30 * 1000);
    await flush();
    expect(reload).toHaveBeenCalledTimes(1);

    jest.advanceTimersByTime(30 * 1000);
    await flush();
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('does not reload the page that pressed the button', async () => {
    renderHook(() => useReloadOnRemoteRefresh());
    await flush();
    expect(await requestRefreshEverywhere()).toBe(true);
    jest.advanceTimersByTime(30 * 1000);
    await flush();
    expect(reload).not.toHaveBeenCalled();
  });
});
