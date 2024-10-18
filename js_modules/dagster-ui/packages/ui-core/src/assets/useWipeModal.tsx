import {Colors, Icon, MenuDivider, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';
import {AssetWipeDialog} from 'shared/assets/AssetWipeDialog.oss';

import {CloudOSSContext} from '../app/CloudOSSContext';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';

export function useWipeModal(
  opts: {assetKey: AssetKeyInput; repository: {location: {name: string}}} | null,
  refresh?: () => void,
) {
  const [showing, setShowing] = useState(false);
  const {
    permissions: {canWipeAssets},
  } = usePermissionsForLocation(opts ? opts.repository.location.name : null);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  return {
    element: (
      <AssetWipeDialog
        assetKeys={opts ? [opts.assetKey] : []}
        isOpen={showing}
        onClose={() => setShowing(false)}
        onComplete={refresh}
      />
    ),
    dropdownOptions:
      opts && canSeeWipeMaterializationAction
        ? [
            <MenuDivider key="wipe-divider" />,
            <MenuItem
              key="wipe"
              text="Wipe materializations"
              icon={<Icon name="delete" color={Colors.accentRed()} />}
              disabled={!canWipeAssets}
              intent="danger"
              onClick={() => setShowing(true)}
            />,
          ]
        : ([] as JSX.Element[]),
  };
}
