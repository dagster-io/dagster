import {LocationBaseDataFetcher} from './LocationBaseDataFetcher';
import {LOCATION_WORKSPACE_QUERY} from './WorkspaceQueries';
import {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables,
  LocationWorkspaceQueryVersion,
} from './types/WorkspaceQueries.types';
import {ApolloClient} from '../../apollo-client';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

export const LOCATION_WORKSPACE_QUERY_KEY = '/LocationWorkspace';

export class WorkspaceLocationDataFetcher extends LocationBaseDataFetcher<
  LocationWorkspaceQuery,
  LocationWorkspaceQueryVariables
> {
  constructor(args: {
    readonly client: ApolloClient<any>;
    readonly localCacheIdPrefix: string | undefined;
    readonly getData: ReturnType<typeof useGetData>;
    readonly statusPoller: WorkspaceStatusPoller;
  }) {
    super({
      query: LOCATION_WORKSPACE_QUERY,
      version: LocationWorkspaceQueryVersion,
      key: `${args.localCacheIdPrefix}${LOCATION_WORKSPACE_QUERY_KEY}`,
      client: args.client,
      statusPoller: args.statusPoller,
      getData: args.getData,
    });
  }

  getVersion(data: LocationWorkspaceQuery) {
    if (data.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry') {
      return data.workspaceLocationEntryOrError.versionKey;
    }
    return '-1';
  }

  getVariables(location: string): LocationWorkspaceQueryVariables {
    return {name: location};
  }
}
