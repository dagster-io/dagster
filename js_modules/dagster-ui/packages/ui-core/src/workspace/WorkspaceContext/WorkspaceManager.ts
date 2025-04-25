import {LocationDataFetcher} from './LocationDataFetcher';
import {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {ApolloClient} from '../../apollo-client';
import {
  CodeLocationStatusQuery,
  LocationStatusEntryFragment,
  LocationWorkspaceQuery,
} from './types/WorkspaceQueries.types';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

type Data = {
  locationStatuses: Record<string, LocationStatusEntryFragment>;
  locationEntryData: Record<string, LocationWorkspaceQuery>;
};
export class WorkspaceManager {
  private statusPoller: WorkspaceStatusPoller;
  private readonly client: ApolloClient<any>;
  private readonly localCacheIdPrefix: string | undefined;
  private readonly getData: ReturnType<typeof useGetData>;
  private readonly setData: (data: Data) => void;
  private dataFetchers: {
    locationEntries: LocationDataFetcher;
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
      locationEntryData: {},
    };
    this.statusPoller = new WorkspaceStatusPoller({
      localCacheIdPrefix: this.localCacheIdPrefix,
      getData: this.getData,
      setCodeLocationStatusAtom: args.setCodeLocationStatusAtom,
    });
    this.dataFetchers = {
      locationEntries: new LocationDataFetcher({
        client: this.client,
        localCacheIdPrefix: this.localCacheIdPrefix,
        getData: this.getData,
        statusPoller: this.statusPoller,
      }),
    };

    this.dataFetchers.locationEntries.subscribe((data) => {
      this.data.locationEntryData = data;
      this.setData(this.data);
    });

    this.statusPoller.subscribe(({locationStatuses}) => {
      this.data.locationStatuses = locationStatuses;
      this.setData(this.data);
    });
  }

  public destroy() {
    this.statusPoller.destroy();
    this.dataFetchers.locationEntries.destroy();
  }
}
