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

    it('retries when the response is for a different version than the status poller reported', async () => {
      // Concurrent loads for one location share a single in-flight query, so a load started
      // after a version change can be served by an older request. The poller won't report that
      // change again, so the fetcher has to notice and ask again itself.
      getData.mockResolvedValueOnce({data: {value: 'previous', version: 'v1'}, error: null});
      getData.mockResolvedValue({data: {value: 'current', version: 'v2'}, error: null});

      fetcher = createFetcher();
      const subscriber = jest.fn();
      fetcher.subscribe(subscriber);
      triggerUpdate();

      await jest.advanceTimersByTimeAsync(0);
      // The response is still committed -- it's newer than nothing -- but it isn't accepted as
      // up to date.
      expect(subscriber).toHaveBeenCalledWith({loc1: {value: 'previous', version: 'v1'}});
      expect(getData).toHaveBeenCalledTimes(1);

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(getData).toHaveBeenCalledTimes(2);
      expect(subscriber).toHaveBeenCalledWith({loc1: {value: 'current', version: 'v2'}});

      await jest.advanceTimersByTimeAsync(RETRY_MAX_INTERVAL * 2);
      expect(getData).toHaveBeenCalledTimes(2);
    });

    it('backs off per location, so a new failure is not delayed by an older one', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      const callsByLocation: Record<string, number> = {loc1: 0, loc2: 0};
      getData.mockImplementation(async ({variables}: {variables: {name: string}}) => {
        const {name} = variables;
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        callsByLocation[name] = callsByLocation[name]! + 1;
        return {data: undefined, error: new Error(`${name} down`)};
      });

      fetcher = createFetcher();
      fetcher.subscribe(jest.fn());

      // Let loc1 fail three times so its next retry is 20s out.
      statusPoller.trigger({
        added: ['loc1'],
        updated: [],
        removed: [],
        locationStatuses: {loc1: {versionKey: 'v1'}},
      });
      await jest.advanceTimersByTimeAsync(0);
      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL); // t=5s, attempt 2
      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL * 2); // t=15s, attempt 3
      expect(callsByLocation.loc1).toBe(3);

      // loc2 starts failing now. It should get its own base-interval retry rather than waiting
      // for loc1's much longer backoff.
      statusPoller.trigger({
        added: ['loc2'],
        updated: [],
        removed: [],
        locationStatuses: {loc1: {versionKey: 'v1'}, loc2: {versionKey: 'v1'}},
      });
      await jest.advanceTimersByTimeAsync(1000);
      expect(callsByLocation.loc2).toBe(1);

      await jest.advanceTimersByTimeAsync(RETRY_BASE_INTERVAL);
      expect(callsByLocation.loc2).toBe(2);
      expect(callsByLocation.loc1).toBe(3);

      fetcher.destroy();
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
