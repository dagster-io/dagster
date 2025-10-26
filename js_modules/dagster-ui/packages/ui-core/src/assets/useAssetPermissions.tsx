import {useMemo} from 'react';

import {gql, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';
import {
  AssetPermissionsQuery,
  AssetPermissionsQueryVariables,
} from './types/useAssetPermissions.types';

interface AssetPermissionsResult {
  hasMaterializePermission: boolean;
  hasWipePermission: boolean;
  hasReportRunlessAssetEventPermission: boolean;
  loading: boolean;
}

/**
 * Hook for fetching asset-specific permissions. If the asset key does not resolve
 * to an asset, falls back to location-level permissions.
 */
export const useAssetPermissions = (
  assetKey: AssetKeyInput,
  locationName: string,
): AssetPermissionsResult => {
  const {permissions: locationPermissions} = usePermissionsForLocation(locationName);

  const {data, loading} = useQuery<AssetPermissionsQuery, AssetPermissionsQueryVariables>(
    ASSET_PERMISSIONS_QUERY,
    {
      variables: {assetKey},
    },
  );

  return useMemo<AssetPermissionsResult>(() => {
    if (data?.assetNodeOrError.__typename === 'AssetNode') {
      return {
        hasMaterializePermission: data.assetNodeOrError.hasMaterializePermission,
        hasWipePermission: data.assetNodeOrError.hasWipePermission,
        hasReportRunlessAssetEventPermission:
          data.assetNodeOrError.hasReportRunlessAssetEventPermission,
        loading,
      };
    }

    return {
      hasMaterializePermission: locationPermissions.canLaunchPipelineExecution,
      hasWipePermission: locationPermissions.canWipeAssets,
      hasReportRunlessAssetEventPermission: locationPermissions.canReportRunlessAssetEvents,
      loading,
    };
  }, [data, loading, locationPermissions]);
};

export const ASSET_PERMISSIONS_QUERY = gql`
  query AssetPermissionsQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        hasMaterializePermission
        hasWipePermission
        hasReportRunlessAssetEventPermission
      }
    }
  }
`;
