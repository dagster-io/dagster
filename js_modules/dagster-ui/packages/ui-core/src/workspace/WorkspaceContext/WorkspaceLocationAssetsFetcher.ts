import {LocationBaseDataFetcher} from './LocationBaseDataFetcher';
import {LOCATION_WORKSPACE_ASSETS_QUERY} from './WorkspaceQueries';
import {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {ApolloClient} from '../../apollo-client';
import {
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceAssetsQueryVariables,
  LocationWorkspaceAssetsQueryVersion,
} from './types/WorkspaceQueries.types';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

export const LOCATION_WORKSPACE_ASSETS_QUERY_KEY = '/LocationWorkspaceAssets';

export class WorkspaceLocationAssetsFetcher extends LocationBaseDataFetcher<
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceAssetsQueryVariables
> {
  constructor(args: {
    readonly client: ApolloClient<any>;
    readonly localCacheIdPrefix: string | undefined;
    readonly getData: ReturnType<typeof useGetData>;
    readonly statusPoller: WorkspaceStatusPoller;
  }) {
    super({
      query: LOCATION_WORKSPACE_ASSETS_QUERY,
      version: LocationWorkspaceAssetsQueryVersion,
      key: `${args.localCacheIdPrefix}${LOCATION_WORKSPACE_ASSETS_QUERY_KEY}`,
      client: args.client,
      statusPoller: args.statusPoller,
      getData: args.getData,
    });
  }

  getVersion(data: LocationWorkspaceAssetsQuery) {
    if (data.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry') {
      return data.workspaceLocationEntryOrError.versionKey;
    }
    return '-1';
  }

  getVariables(location: string): LocationWorkspaceAssetsQueryVariables {
    return {name: location};
  }
}
