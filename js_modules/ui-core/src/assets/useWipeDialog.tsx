import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {AssetWipeDialog} from '@shared/assets/AssetWipeDialog';
import {useContext, useState} from 'react';

import {assetHasWipePermission} from './assetWipePermissions';
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

  const hasWipePermission = opts
    ? assetHasWipePermission(opts, unscopedPermissions, locationPermissions)
    : false;

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
