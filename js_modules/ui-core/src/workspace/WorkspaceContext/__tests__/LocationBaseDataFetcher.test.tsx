import {waitFor} from '@testing-library/react';

import {ApolloClient, DocumentNode} from '../../../apollo-client';
import {
  LocationBaseDataFetcher,
  RETRY_BASE_INTERVAL,
  RETRY_MAX_INTERVAL,
} from '../LocationBaseDataFetcher';
import type {WorkspaceStatusPoller} from '../WorkspaceStatusPoller';
import type {LocationStatusEntryFragment} from '../types/WorkspaceQueries.types';

const mockClearCachedData = jest.fn();
const mockGetCachedData = jest.fn();

jest.mock('../../../search/useIndexedDBCachedQuery', () => ({
  clearCachedData: (...args: unknown[]) => mockClearCachedData(...args),
  getCachedData: (...args: unknown[]) => mockGetCachedData(...args),
}));

interface StatusUpdate {
  added: string[];
  updated: string[];
  removed: string[];
  locationStatuses: Record<string, Partial<LocationStatusEntryFragment>>;
}

// Add a mock status poller class
class MockStatusPoller {
  private subscriber: ((update: StatusUpdate) => void) | null = null;
  subscribe = jest.fn((cb: (update: StatusUpdate) => void) => {
    this.subscriber = cb;
    return this.unsubscribe;
  });
  destroy = jest.fn();
  unsubscribe = jest.fn(() => {
    this.subscriber = null;
  });
  trigger(update: StatusUpdate) {
    if (this.subscriber) {
      this.subscriber(update);
    }
  }
}

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});

type TestData = {value: string; version: string};
type TestVariables = {name: string};

class TestDataFetcher extends LocationBaseDataFetcher<TestData, TestVariables> {
  getVariables(location: string): TestVariables {
    return {name: location};
  }
  getVersion(data: TestData): string {
    return data.version;
  }
}

const getData = jest.fn();
describe('LocationBaseDataFetcher', () => {
  let fetcher: TestDataFetcher;
  let statusPoller: MockStatusPoller;

  function createFetcher() {
    statusPoller = new MockStatusPoller();
    return new TestDataFetcher({
      query: {} as unknown as DocumentNode,
      version: '1',
      client: {} as unknown as ApolloClient<unknown>,
      statusPoller: statusPoller as unknown as WorkspaceStatusPoller,
      getData,
      key: 'test-key',
    });
  }

  it('subscribes to statusPoller on construction', () => {
    fetcher = createFetcher();
    expect(statusPoller.subscribe).toHaveBeenCalled();
  });

  it('notifies subscribers with data', async () => {
    getData.mockResolvedValue({data: {value: 'foo', version: 'v1'}, error: null});
    fetcher = createFetcher();
    const subscriber = jest.fn();
    fetcher.subscribe(subscriber);
    statusPoller.trigger({
      added: ['loc1'],
      updated: [],
      removed: [],
      locationStatuses: {loc1: {versionKey: 'v1'}},
    });
    await waitFor(() => {
      expect(subscriber).toHaveBeenCalledWith({loc1: {value: 'foo', version: 'v1'}});
    });
  });

  it('loads from cache before server', async () => {
    mockGetCachedData.mockResolvedValue({value: 'cached', version: 'v2'});
    getData.mockResolvedValue({data: {value: 'bar', version: 'v2'}, error: null});
    fetcher = createFetcher();
    const subscriber = jest.fn();
    fetcher.subscribe(subscriber);
    statusPoller.trigger({
      added: ['loc2'],
      updated: [],
      removed: [],
      locationStatuses: {loc2: {versionKey: 'v2'}},
    });
    await Promise.resolve();
    expect(subscriber).toHaveBeenCalled();
  });

  it('does not load from server if version is unchanged', async () => {
    mockGetCachedData.mockResolvedValue({value: 'cached', version: 'v3'});
    getData.mockResolvedValue({data: {value: 'cached', version: 'v3'}, error: null});
    fetcher = createFetcher();
    const subscriber = jest.fn();
    fetcher.subscribe(subscriber);
    statusPoller.trigger({
      added: ['loc3'],
      updated: [],
      removed: [],
      locationStatuses: {loc3: {versionKey: 'v3'}},
    });

    await Promise.resolve();
    expect(mockGetCachedData).toHaveBeenCalled();
    expect(getData).not.toHaveBeenCalled();
  });

  it('removes data and clears cache for removed locations', async () => {
    getData.mockResolvedValue({data: {value: 'baz', version: 'v4'}, error: null});
    fetcher = createFetcher();
    const subscriber = jest.fn();
    fetcher.subscribe(subscriber);
    statusPoller.trigger({
      added: ['loc4'],
      updated: [],
      removed: [],
      locationStatuses: {loc4: {versionKey: 'v4'}},
    });
    statusPoller.trigger({added: [], updated: [], removed: ['loc4'], locationStatuses: {}});
    expect(mockClearCachedData).toHaveBeenCalledWith({key: 'test-key/loc4'});
    expect(subscriber).toHaveBeenCalledWith({});
  });

  it('unsubscribes correctly', () => {
    fetcher = createFetcher();
    fetcher.destroy();
    expect(statusPoller.unsubscribe).toHaveBeenCalled();
  });

  describe('retrying failed locations', () => {
    beforeEach(() => {
      jest.useFakeTimers();
      mockGetCachedData.mockResolvedValue(undefined);
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    const triggerUpdate = () => {
      statusPoller.trigger({
        added: ['loc1'],
        updated: [],
        removed: [],
        locationStatuses: {loc1: {versionKey: 'v2'}},
      });
    };

    it('retries a location whose fetch errored, and notifies once it succeeds', async () => {
      // The status poller only reports a location when its versionKey *changes*, so a dropped
      // failure would leave the UI rendering the previous deployment's definitions forever.
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      getData.mockResolvedValueOnce({data: undefined, error: new Error('code server down')});
      getData.mockResolvedValue({data: {value: 'fresh', version: 'v2'}, error: null});

      fetcher = createFetcher();
      const subscriber = jest.fn();
      fetcher.subscribe(subscriber);
      triggerUpdate();

      await jest.advanceTimersByTimeAsync(0);
      expect(getData).toHaveBeenCalledTimes(1);
      expect(subscriber).not.toHaveBeenCalledWith({loc1: {value: 'fresh', version: 'v2'}});

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(2);
      expect(subscriber).toHaveBeenCalledWith({loc1: {value: 'fresh', version: 'v2'}});

      // Once the location loads there is nothing left to retry.
      await jest.advanceTimersByTimeAsync(RETRY_MAX_INTERVAL * 2);
      expect(getData).toHaveBeenCalledTimes(2);
      consoleError.mockRestore();
    });

    it('retries a location that returned neither data nor an error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      getData.mockResolvedValueOnce({data: undefined, error: null});
      getData.mockResolvedValue({data: {value: 'fresh', version: 'v2'}, error: null});

      fetcher = createFetcher();
      fetcher.subscribe(jest.fn());
      triggerUpdate();

      await jest.advanceTimersByTimeAsync(0);
      expect(getData).toHaveBeenCalledTimes(1);

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(2);
      consoleError.mockRestore();
    });

    it('backs off between retries and stops once destroyed', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      getData.mockResolvedValue({data: undefined, error: new Error('still down')});

      fetcher = createFetcher();
      fetcher.subscribe(jest.fn());
      triggerUpdate();

      await jest.advanceTimersByTimeAsync(0);
      expect(getData).toHaveBeenCalledTimes(1);

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(2);

      // The next retry waits twice as long, so nothing happens at the base interval.
      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(2);

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(3);

      fetcher.destroy();
      await jest.advanceTimersByTimeAsync(RETRY_MAX_INTERVAL * 4);
      expect(getData).toHaveBeenCalledTimes(3);
      consoleError.mockRestore();
    });

    it('stops retrying a location that was removed', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      getData.mockResolvedValue({data: undefined, error: new Error('code server down')});

      fetcher = createFetcher();
      fetcher.subscribe(jest.fn());
      triggerUpdate();

      await jest.advanceTimersByTimeAsync(0);
      expect(getData).toHaveBeenCalledTimes(1);

      statusPoller.trigger({added: [], updated: [], removed: ['loc1'], locationStatuses: {}});
      await jest.advanceTimersByTimeAsync(RETRY_MAX_INTERVAL * 2);
      expect(getData).toHaveBeenCalledTimes(1);
      consoleError.mockRestore();
    });
  });
});
