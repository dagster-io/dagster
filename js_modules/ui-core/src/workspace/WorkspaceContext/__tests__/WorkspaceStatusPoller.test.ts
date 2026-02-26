import {CODE_LOCATION_STATUS_QUERY_KEY, WorkspaceStatusPoller} from '../WorkspaceStatusPoller';
import {
  CodeLocationStatusQueryVersion,
  LocationStatusEntryFragment,
} from '../types/WorkspaceQueries.types';
import {RepositoryLocationLoadStatus} from './../../../graphql/types';

jest.useFakeTimers();

const mockGetCachedData = jest.fn();
const mockGetData = jest.fn();
const mockSetCodeLocationStatusAtom = jest.fn();

jest.mock('../../../search/useIndexedDBCachedQuery', () => ({
  getCachedData: (...args: any[]) => mockGetCachedData(...args),
  useGetData: () => mockGetData,
}));

describe('WorkspaceStatusPoller', () => {
  const localCacheIdPrefix = 'testPrefix';
  const key = `${localCacheIdPrefix}${CODE_LOCATION_STATUS_QUERY_KEY}`;
  let poller: WorkspaceStatusPoller;

  const makeStatus = (name: string, versionKey: string): LocationStatusEntryFragment => ({
    __typename: 'WorkspaceLocationStatusEntry',
    id: name,
    name,
    loadStatus: RepositoryLocationLoadStatus.LOADED,
    updateTimestamp: 1,
    versionKey,
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    if (poller) {
      poller.destroy();
    }
  });

  it('loads from cache and notifies subscribers', async () => {
    const cached = {
      locationStatusesOrError: {
        __typename: 'WorkspaceLocationStatusEntries',
        entries: [makeStatus('loc1', 'v1')],
      },
    };
    mockGetCachedData.mockResolvedValueOnce(cached);
    mockGetData.mockResolvedValue({data: undefined, error: new Error('test error')});
    const subscriber = jest.fn();
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    await Promise.resolve();
    poller.subscribe(subscriber);
    expect(mockGetCachedData).toHaveBeenCalledWith({key, version: CodeLocationStatusQueryVersion});
    expect(mockSetCodeLocationStatusAtom).toHaveBeenCalledWith(cached);
    expect(subscriber).toHaveBeenCalledWith({
      added: ['loc1'],
      updated: [],
      removed: [],
      locationStatuses: {loc1: makeStatus('loc1', 'v1')},
    });
    expect(mockGetData).toHaveBeenCalled();
  });

  it('loads from server and notifies subscribers on changes', async () => {
    mockGetCachedData.mockResolvedValue(undefined);
    const serverData = {
      locationStatusesOrError: {
        __typename: 'WorkspaceLocationStatusEntries',
        entries: [makeStatus('loc2', 'v2')],
      },
    };
    mockGetData.mockResolvedValueOnce({data: serverData, error: undefined});
    const subscriber = jest.fn();
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    await Promise.resolve(); // allow async server load
    poller.subscribe(subscriber);
    jest.advanceTimersByTime(5000); // trigger poll interval
    await Promise.resolve();
    expect(mockGetData).toHaveBeenCalledWith({
      query: expect.anything(),
      key,
      version: CodeLocationStatusQueryVersion,
      bypassCache: true,
    });
    expect(subscriber).toHaveBeenCalledWith({
      added: ['loc2'],
      updated: [],
      removed: [],
      locationStatuses: {loc2: makeStatus('loc2', 'v2')},
    });
  });

  it('notifies on updated and removed locations', async () => {
    mockGetCachedData.mockResolvedValue(undefined);
    // First poll: loc1 v1
    const first = {
      locationStatusesOrError: {
        __typename: 'WorkspaceLocationStatusEntries',
        entries: [makeStatus('loc1', 'v1')],
      },
    };
    // Second poll: loc1 v2, loc2 v1
    const second = {
      locationStatusesOrError: {
        __typename: 'WorkspaceLocationStatusEntries',
        entries: [makeStatus('loc1', 'v2'), makeStatus('loc2', 'v1')],
      },
    };
    const third = {
      locationStatusesOrError: {
        __typename: 'WorkspaceLocationStatusEntries',
        entries: [makeStatus('loc1', 'v2')],
      },
    };
    mockGetData
      .mockResolvedValueOnce({data: first, error: undefined})
      .mockResolvedValueOnce({data: second, error: undefined})
      .mockResolvedValueOnce({data: third, error: undefined});
    const subscriber = jest.fn();
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    await Promise.resolve();
    poller.subscribe(subscriber);
    jest.advanceTimersByTime(10000); // trigger second and third poll
    await Promise.resolve();
    expect(subscriber).toHaveBeenCalledWith({
      added: ['loc1'],
      updated: [],
      removed: [],
      locationStatuses: {loc1: makeStatus('loc1', 'v1')},
    });
    expect(subscriber).toHaveBeenCalledWith({
      added: ['loc2'],
      updated: ['loc1'],
      removed: [],
      locationStatuses: {loc1: makeStatus('loc1', 'v2'), loc2: makeStatus('loc2', 'v1')},
    });
    expect(subscriber).toHaveBeenCalledWith({
      added: [],
      updated: [],
      removed: ['loc2'],
      locationStatuses: {loc1: makeStatus('loc1', 'v2')},
    });
  });

  it('unsubscribes correctly', async () => {
    mockGetCachedData.mockResolvedValue(undefined);
    mockGetData.mockResolvedValue({data: undefined, error: new Error('test error')});
    const subscriber = jest.fn();
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    const unsubscribe = poller.subscribe(subscriber);
    unsubscribe();
    poller['notifySubscribers']();
    expect(subscriber).toHaveBeenCalledTimes(0);
  });

  it('cleans up interval on destroy', () => {
    mockGetCachedData.mockResolvedValue(undefined);
    mockGetData.mockResolvedValue({data: undefined, error: new Error('test error')});
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    const clearSpy = jest.spyOn(global, 'clearInterval');
    poller.destroy();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it('does not poll when document is hidden', () => {
    mockGetCachedData.mockResolvedValue(undefined);
    mockGetData.mockResolvedValue({data: undefined, error: new Error('test error')});
    jest.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden');
    poller = new WorkspaceStatusPoller({
      localCacheIdPrefix,
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    jest.advanceTimersByTime(10000);
    expect(mockGetData).not.toHaveBeenCalled();
  });
});
