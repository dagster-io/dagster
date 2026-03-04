import {ApolloClient} from '../../../apollo-client';
import {WorkspaceLocationAssetsFetcher} from '../WorkspaceLocationAssetsFetcher';
import {WorkspaceLocationDataFetcher} from '../WorkspaceLocationDataFetcher';
import {WorkspaceManager} from '../WorkspaceManager';
import {WorkspaceStatusPoller} from '../WorkspaceStatusPoller';

jest.mock('../WorkspaceLocationDataFetcher');
jest.mock('../WorkspaceStatusPoller');
jest.mock('../WorkspaceLocationAssetsFetcher');

describe('WorkspaceManager', () => {
  let mockClient: ApolloClient<any>;
  let mockGetData: jest.Mock;
  let mockSetData: jest.Mock;
  let mockSetCodeLocationStatusAtom: jest.Mock;
  let mockStatusPoller: any;
  let mockWorkspaceLocationDataFetcher: any;
  let mockWorkspaceLocationAssetsFetcher: any;
  beforeEach(() => {
    jest.clearAllMocks();
    mockClient = {} as any;
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
    });
  });

  it('subscribes to data fetcher and poller and updates data', () => {
    let dataFetcherCallback: any;
    let pollerCallback: any;
    let assetsFetcherCallback: any;

    mockWorkspaceLocationDataFetcher.subscribe.mockImplementation((cb: any) => {
      dataFetcherCallback = cb;
    });
    mockStatusPoller.subscribe.mockImplementation((cb: any) => {
      pollerCallback = cb;
    });
    mockWorkspaceLocationAssetsFetcher.subscribe.mockImplementation((cb: any) => {
      assetsFetcherCallback = cb;
    });
    new WorkspaceManager({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      setData: mockSetData,
      setCodeLocationStatusAtom: mockSetCodeLocationStatusAtom,
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
    });

    manager.destroy();
    expect(mockStatusPoller.destroy).toHaveBeenCalled();
    expect(mockWorkspaceLocationDataFetcher.destroy).toHaveBeenCalled();
  });
});
