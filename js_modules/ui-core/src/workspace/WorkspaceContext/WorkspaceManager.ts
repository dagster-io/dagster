import {WorkspaceLocationAssetsFetcher} from './WorkspaceLocationAssetsFetcher';
import {WorkspaceLocationDataFetcher} from './WorkspaceLocationDataFetcher';
import {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {ApolloClient} from '../../apollo-client';
import {
  CodeLocationStatusQuery,
  LocationStatusEntryFragment,
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceQuery,
} from './types/WorkspaceQueries.types';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

type Data = Partial<{
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  locationEntries: Record<string, LocationWorkspaceQuery>;
  assetEntries: Record<string, LocationWorkspaceAssetsQuery>;
}>;
export class WorkspaceManager {
  private statusPoller: WorkspaceStatusPoller;
  private readonly client: ApolloClient<any>;
  private readonly localCacheIdPrefix: string | undefined;
  private readonly getData: ReturnType<typeof useGetData>;
  private readonly setData: (data: Data) => void;
  private dataFetchers: {
    locationEntries: WorkspaceLocationDataFetcher;
    assetEntries: WorkspaceLocationAssetsFetcher;
  };
  private readonly data: Data;

  constructor(args: {
    readonly client: ApolloClient<any>;
    readonly localCacheIdPrefix: string | undefined;
    readonly getData: ReturnType<typeof useGetData>;
    readonly setData: (data: Data) => void;
    readonly setCodeLocationStatusAtom: (status: CodeLocationStatusQuery) => void;
  }) {
    this.client = args.client;
    this.localCacheIdPrefix = args.localCacheIdPrefix;
    this.getData = args.getData;
    this.setData = args.setData;
    this.data = {
      locationStatuses: {},
      locationEntries: {},
      assetEntries: {},
    };
    this.statusPoller = new WorkspaceStatusPoller({
      localCacheIdPrefix: this.localCacheIdPrefix,
      getData: this.getData,
      setCodeLocationStatusAtom: args.setCodeLocationStatusAtom,
    });
    this.dataFetchers = {
      locationEntries: new WorkspaceLocationDataFetcher({
        client: this.client,
        localCacheIdPrefix: this.localCacheIdPrefix,
        getData: this.getData,
        statusPoller: this.statusPoller,
      }),
      assetEntries: new WorkspaceLocationAssetsFetcher({
        client: this.client,
        localCacheIdPrefix: this.localCacheIdPrefix,
        getData: this.getData,
        statusPoller: this.statusPoller,
      }),
    };

    Object.entries(this.dataFetchers).forEach(([key, fetcher]) => {
      fetcher.subscribe((data) => {
        this.setData({[key]: data});
      });
    });

    this.statusPoller.subscribe(async ({locationStatuses}) => {
      this.data.locationStatuses = locationStatuses;
      this.setData({locationStatuses});
    });
  }

  public async refetchAll() {
    await this.statusPoller.refetch();
  }

  public destroy() {
    this.statusPoller.destroy();
    Object.values(this.dataFetchers).forEach((fetcher) => {
      fetcher.destroy();
    });
  }
}
