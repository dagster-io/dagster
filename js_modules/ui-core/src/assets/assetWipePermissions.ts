import {PermissionsMap} from '../app/Permissions';

type AssetWipePermission = {
  definitionHasWipePermission: boolean;
  locationName?: string | null;
};

type WipePermissions = Pick<PermissionsMap, 'canWipeAssets'>;

export const assetHasWipePermission = (
  asset: AssetWipePermission,
  unscopedPermissions: WipePermissions,
  locationPermissions: Record<string, WipePermissions>,
) => {
  return !!(
    unscopedPermissions.canWipeAssets.enabled ||
    (asset.locationName && locationPermissions[asset.locationName]?.canWipeAssets.enabled) ||
    asset.definitionHasWipePermission
  );
};
