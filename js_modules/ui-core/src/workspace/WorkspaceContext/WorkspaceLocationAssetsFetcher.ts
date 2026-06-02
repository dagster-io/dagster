import {LocationBaseDataFetcher} from './LocationBaseDataFetcher';
import {
  LOCATION_WORKSPACE_ASSETS_MANIFEST_QUERY,
  LOCATION_WORKSPACE_ASSETS_QUERY,
} from './WorkspaceQueries';
import {WorkspaceStatusPoller} from './WorkspaceStatusPoller';
import {ApolloClient} from '../../apollo-client';
import {
  LocationWorkspaceAssetsManifestQuery,
  LocationWorkspaceAssetsManifestQueryVersion,
  LocationWorkspaceAssetsQuery,
  LocationWorkspaceAssetsQueryVariables,
  LocationWorkspaceAssetsQueryVersion,
} from './types/WorkspaceQueries.types';
import {useGetData} from '../../search/useIndexedDBCachedQuery';

export const LOCATION_WORKSPACE_ASSETS_QUERY_KEY = '/LocationWorkspaceAssets';
export const LOCATION_WORKSPACE_ASSETS_MANIFEST_QUERY_KEY = '/LocationWorkspaceAssetsManifest';

export type RawWorkspaceAssetsResponse =
  | LocationWorkspaceAssetsQuery
  | LocationWorkspaceAssetsManifestQuery;

export class WorkspaceLocationAssetsFetcher extends LocationBaseDataFetcher<
  RawWorkspaceAssetsResponse,
  LocationWorkspaceAssetsQueryVariables
> {
  constructor(args: {
    readonly client: ApolloClient<any>;
    readonly localCacheIdPrefix: string | undefined;
    readonly getData: ReturnType<typeof useGetData>;
    readonly statusPoller: WorkspaceStatusPoller;
    readonly shouldUseAssetManifest: boolean;
  }) {
    const keySuffix = args.shouldUseAssetManifest
      ? LOCATION_WORKSPACE_ASSETS_MANIFEST_QUERY_KEY
      : LOCATION_WORKSPACE_ASSETS_QUERY_KEY;
    super({
      query: args.shouldUseAssetManifest
        ? LOCATION_WORKSPACE_ASSETS_MANIFEST_QUERY
        : LOCATION_WORKSPACE_ASSETS_QUERY,
      version: args.shouldUseAssetManifest
        ? LocationWorkspaceAssetsManifestQueryVersion
        : LocationWorkspaceAssetsQueryVersion,
      key: `${args.localCacheIdPrefix}${keySuffix}`,
      client: args.client,
      statusPoller: args.statusPoller,
      getData: args.getData,
    });
  }

  getVersion(data: RawWorkspaceAssetsResponse) {
    if (data.workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry') {
      return data.workspaceLocationEntryOrError.versionKey;
    }
    return '-1';
  }

  getVariables(location: string): LocationWorkspaceAssetsQueryVariables {
    return {name: location};
  }
}
