import {useMemo} from 'react';

import {gql, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';
import {
  AssetPermissionsQuery,
  AssetPermissionsQueryVariables,
} from './types/useAssetPermissions.types';

export const useAssetPermissions = (assetKey: AssetKeyInput, locationName: string) => {
  const {permissions: locationPermissions, loading: locationLoading} =
    usePermissionsForLocation(locationName);

  const {data, loading} = useQuery<AssetPermissionsQuery, AssetPermissionsQueryVariables>(
    ASSET_PERMISSIONS_QUERY,
    {
      variables: {assetKey: {path: assetKey.path}},
    },
  );

  const {canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents} =
    locationPermissions;
  const fallbackPermissions = useMemo(() => {
    return {canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents};
  }, [canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents]);

  return useMemo(() => {
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
      hasMaterializePermission: fallbackPermissions.canLaunchPipelineExecution,
      hasWipePermission: fallbackPermissions.canWipeAssets,
      hasReportRunlessAssetEventPermission: fallbackPermissions.canReportRunlessAssetEvents,
      loading: loading || locationLoading,
    };
  }, [data, loading, locationLoading, fallbackPermissions]);
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
