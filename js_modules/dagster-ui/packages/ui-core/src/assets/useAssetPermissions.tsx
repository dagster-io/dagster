import {useMemo} from 'react';

import {gql, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';
import {
  AssetsPermissionsQuery,
  AssetsPermissionsQueryVariables,
} from './types/useAssetPermissions.types';

export const useAssetPermissions = (assetKeys: AssetKeyInput[], locationName: string) => {
  const {permissions: locationPermissions, loading: locationLoading} =
    usePermissionsForLocation(locationName);

  const {data, loading} = useQuery<AssetsPermissionsQuery, AssetsPermissionsQueryVariables>(
    ASSETS_PERMISSIONS_QUERY,
    {
      variables: {assetKeys: assetKeys.map((key) => ({path: key.path}))},
      skip: assetKeys.length === 0,
    },
  );

  const {canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents} =
    locationPermissions;
  const fallbackPermissions = useMemo(() => {
    return {canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents};
  }, [canLaunchPipelineExecution, canWipeAssets, canReportRunlessAssetEvents]);

  return useMemo(() => {
    // If no asset keys provided, fall back to location permissions
    if (assetKeys.length === 0) {
      return {
        hasMaterializePermission: fallbackPermissions.canLaunchPipelineExecution,
        hasWipePermission: fallbackPermissions.canWipeAssets,
        hasReportRunlessAssetEventPermission: fallbackPermissions.canReportRunlessAssetEvents,
        loading: locationLoading,
      };
    }

    // Collect permissions from all assets
    const assetNodes = data?.assetNodes || [];

    // If we don't have data for all assets yet, use fallback
    if (assetNodes.length !== assetKeys.length) {
      return {
        hasMaterializePermission: fallbackPermissions.canLaunchPipelineExecution,
        hasWipePermission: fallbackPermissions.canWipeAssets,
        hasReportRunlessAssetEventPermission: fallbackPermissions.canReportRunlessAssetEvents,
        loading: loading || locationLoading,
      };
    }

    // Permission is allowed only if ALL assets allow it
    const hasMaterializePermission = assetNodes.every((node) => node.hasMaterializePermission);
    const hasWipePermission = assetNodes.every((node) => node.hasWipePermission);
    const hasReportRunlessAssetEventPermission = assetNodes.every(
      (node) => node.hasReportRunlessAssetEventPermission,
    );

    return {
      hasMaterializePermission,
      hasWipePermission,
      hasReportRunlessAssetEventPermission,
      loading,
    };
  }, [data, loading, locationLoading, fallbackPermissions, assetKeys]);
};

export const ASSETS_PERMISSIONS_QUERY = gql`
  query AssetsPermissionsQuery($assetKeys: [AssetKeyInput!]!) {
    assetNodes(assetKeys: $assetKeys) {
      id
      hasMaterializePermission
      hasWipePermission
      hasReportRunlessAssetEventPermission
    }
  }
`;
