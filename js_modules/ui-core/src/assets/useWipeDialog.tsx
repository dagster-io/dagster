import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {AssetWipeDialog} from '@shared/assets/AssetWipeDialog';
import {useContext, useState} from 'react';

import {CloudOSSContext} from '../app/CloudOSSContext';
import {PermissionsContext} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';

export const useWipeDialog = (
  opts: {
    assetKey: AssetKeyInput;
    definitionHasWipePermission: boolean;
    locationName: string | null;
  } | null,
  refresh?: () => void,
) => {
  const [isShowing, setIsShowing] = useState(false);
  const {unscopedPermissions, locationPermissions} = useContext(PermissionsContext);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  // Allow if any permission level grants access:
  // 1. Deployment-wide (unscoped) permission
  // 2. Code location permission
  // 3. Per-asset permission from definition (owner-based)
  const hasWipePermission =
    unscopedPermissions.canWipeAssets?.enabled ||
    (opts?.locationName && locationPermissions[opts.locationName]?.canWipeAssets?.enabled) ||
    !!opts?.definitionHasWipePermission;

  return {
    element: (
      <AssetWipeDialog
        assetKeys={opts ? [opts.assetKey] : []}
        isOpen={isShowing}
        onClose={() => setIsShowing(false)}
        onComplete={refresh}
      />
    ),
    dropdownOptions:
      opts && canSeeWipeMaterializationAction
        ? [
            <MenuItem
              key="wipe"
              text="Wipe materializations"
              icon={<Icon name="delete" color={Colors.accentRed()} />}
              disabled={!hasWipePermission}
              intent="danger"
              onClick={() => setIsShowing(true)}
            />,
          ]
        : [],
  };
};
