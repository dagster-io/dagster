import {waitFor} from '@testing-library/react';

import {LocationBaseDataFetcher} from '../LocationBaseDataFetcher';

const mockClearCachedData = jest.fn();
const mockGetCachedData = jest.fn();

jest.mock('../../../search/useIndexedDBCachedQuery', () => ({
  clearCachedData: (...args: any[]) => mockClearCachedData(...args),
  getCachedData: (...args: any[]) => mockGetCachedData(...args),
}));

// Add a mock status poller class
class MockStatusPoller {
  private subscriber: ((update: any) => void) | null = null;
  subscribe = jest.fn((cb: any) => {
    this.subscriber = cb;
    return this.unsubscribe;
  });
  destroy = jest.fn();
  unsubscribe = jest.fn(() => {
    this.subscriber = null;
  });
  trigger(update: any) {
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
  let statusPoller: any;

  function createFetcher() {
    statusPoller = new MockStatusPoller();
    return new TestDataFetcher({
      query: {} as any,
      version: '1',
      client: {} as any,
      statusPoller,
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
});
