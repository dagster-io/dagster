import {ApolloClient} from '../../../apollo-client';
import {WorkspaceLocationAssetsFetcher} from '../WorkspaceLocationAssetsFetcher';
import {WorkspaceLocationDataFetcher} from '../WorkspaceLocationDataFetcher';
import {WorkspaceManager} from '../WorkspaceManager';
import {WorkspaceStatusPoller} from '../WorkspaceStatusPoller';

jest.mock('../WorkspaceLocationDataFetcher');
jest.mock('../WorkspaceStatusPoller');
jest.mock('../WorkspaceLocationAssetsFetcher');

interface MockSubscribable {
  subscribe: jest.Mock;
  destroy: jest.Mock;
}

describe('WorkspaceManager', () => {
  let mockClient: ApolloClient<unknown>;
  let mockGetData: jest.Mock;
  let mockSetData: jest.Mock;
  let mockSetCodeLocationStatusAtom: jest.Mock;
  let mockStatusPoller: MockSubscribable;
  let mockWorkspaceLocationDataFetcher: MockSubscribable;
  let mockWorkspaceLocationAssetsFetcher: MockSubscribable;
  beforeEach(() => {
    jest.clearAllMocks();
    mockClient = {} as unknown as ApolloClient<unknown>;
    mockGetData = jest.fn();
    mockSetData = jest.fn();
    mockSetCodeLocationStatusAtom = jest.fn();

    // Mock the WorkspaceStatusPoller
    mockStatusPoller = {
      subscribe: jest.fn(),
      destroy: jest.fn(),
    };
    (WorkspaceStatusPoller as jest.Mock).mockImplementation(() => {
      return mockStatusPoller;
    });

    // Mock the WorkspaceLocationDataFetcher
    mockWorkspaceLocationDataFetcher = {
      subscribe: jest.fn(),
      destroy: jest.fn(),
    };
    (WorkspaceLocationDataFetcher as jest.Mock).mockImplementation(() => {
      return mockWorkspaceLocationDataFetcher;
    });

    mockWorkspaceLocationAssetsFetcher = {
      subscribe: jest.fn(),
      destroy: jest.fn(),
    };
    (WorkspaceLocationAssetsFetcher as jest.Mock).mockImplementation(() => {
      return mockWorkspaceLocationAssetsFetcher;
    });
  });

  it('initializes poller and data fetcher with correct arguments', () => {
    new WorkspaceManager({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      setData: mockSetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
      shouldUseAssetManifest: false,
    });

    expect(WorkspaceStatusPoller).toHaveBeenCalledWith({
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
    });
    expect(WorkspaceLocationDataFetcher).toHaveBeenCalledWith({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      statusPoller: mockStatusPoller,
    });
    expect(WorkspaceLocationAssetsFetcher).toHaveBeenCalledWith({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      statusPoller: mockStatusPoller,
      shouldUseAssetManifest: false,
    });
  });

  it('subscribes to data fetcher and poller and updates data', () => {
    let dataFetcherCallback: (data: Record<string, unknown>) => void = () => {};
    let pollerCallback: (data: Record<string, unknown>) => void = () => {};
    let assetsFetcherCallback: (data: Record<string, unknown>) => void = () => {};

    mockWorkspaceLocationDataFetcher.subscribe.mockImplementation(
      (cb: (data: Record<string, unknown>) => void) => {
        dataFetcherCallback = cb;
      },
    );
    mockStatusPoller.subscribe.mockImplementation((cb: (data: Record<string, unknown>) => void) => {
      pollerCallback = cb;
    });
    mockWorkspaceLocationAssetsFetcher.subscribe.mockImplementation(
      (cb: (data: Record<string, unknown>) => void) => {
        assetsFetcherCallback = cb;
      },
    );
    new WorkspaceManager({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      setData: mockSetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
      shouldUseAssetManifest: false,
    });

    // Simulate data fetcher update
    dataFetcherCallback({foo: 'bar'});
    expect(mockSetData).toHaveBeenCalledWith(
      expect.objectContaining({
        locationEntries: {foo: 'bar'},
      }),
    );

    // Simulate assets fetcher update
    assetsFetcherCallback({foo: 'bar'});
    expect(mockSetData).toHaveBeenCalledWith(
      expect.objectContaining({
        assetEntries: {foo: 'bar'},
      }),
    );

    // Simulate poller update
    pollerCallback({locationStatuses: {loc1: {name: 'loc1', versionKey: 'v1'}}});
    expect(mockSetData).toHaveBeenCalledWith(
      expect.objectContaining({
        locationStatuses: {loc1: {name: 'loc1', versionKey: 'v1'}},
      }),
    );
  });

  it('calls destroy on poller and data fetcher', () => {
    const manager = new WorkspaceManager({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      setData: mockSetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
      shouldUseAssetManifest: false,
    });

    manager.destroy();
    expect(mockStatusPoller.destroy).toHaveBeenCalled();
    expect(mockWorkspaceLocationDataFetcher.destroy).toHaveBeenCalled();
  });
});
