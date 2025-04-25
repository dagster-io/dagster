import {ApolloClient} from '../../../apollo-client';
import {LocationDataFetcher} from '../LocationDataFetcher';
import {WorkspaceManager} from '../WorkspaceManager';
import {WorkspaceStatusPoller} from '../WorkspaceStatusPoller';

jest.mock('../LocationDataFetcher');
jest.mock('../WorkspaceStatusPoller');

describe('WorkspaceManager', () => {
  let mockClient: ApolloClient<any>;
  let mockGetData: jest.Mock;
  let mockSetData: jest.Mock;
  let mockSetCodeLocationStatusAtom: jest.Mock;
  let mockStatusPoller: any;
  let mockLocationDataFetcher: any;

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

    // Mock the LocationDataFetcher
    mockLocationDataFetcher = {
      subscribe: jest.fn(),
      destroy: jest.fn(),
    };
    (LocationDataFetcher as jest.Mock).mockImplementation(() => {
      return mockLocationDataFetcher;
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
    expect(LocationDataFetcher).toHaveBeenCalledWith({
      client: mockClient,
      localCacheIdPrefix: 'prefix',
      getData: mockGetData,
      statusPoller: mockStatusPoller,
    });
  });

  it('subscribes to data fetcher and poller and updates data', () => {
    let dataFetcherCallback: any;
    let pollerCallback: any;

    mockLocationDataFetcher.subscribe.mockImplementation((cb: any) => {
      dataFetcherCallback = cb;
    });
    mockStatusPoller.subscribe.mockImplementation((cb: any) => {
      pollerCallback = cb;
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
      expect.objectContaining({locationEntryData: {foo: 'bar'}}),
    );

    // Simulate poller update
    pollerCallback({locationStatuses: {loc1: {name: 'loc1', versionKey: 'v1'}}});
    expect(mockSetData).toHaveBeenCalledWith(
      expect.objectContaining({locationStatuses: {loc1: {name: 'loc1', versionKey: 'v1'}}}),
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
    expect(mockLocationDataFetcher.destroy).toHaveBeenCalled();
  });
});
