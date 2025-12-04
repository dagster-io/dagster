import {Colors, Icon, MenuDivider, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';
import {AssetWipeDialog} from 'shared/assets/AssetWipeDialog.oss';

import {useAssetPermissions} from './useAssetPermissions';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {AssetKeyInput} from '../graphql/types';

export function useWipeDialog(
  opts: {assetKey: AssetKeyInput; repository: {location: {name: string}} | null} | null,
  refresh?: () => void,
) {
  const [showing, setShowing] = useState(false);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  const {hasWipePermission} = useAssetPermissions(
    opts?.assetKey ? [opts.assetKey] : [],
    opts?.repository?.location.name || '',
  );

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
              disabled={!hasWipePermission}
              intent="danger"
              onClick={() => setShowing(true)}
            />,
          ]
        : ([] as JSX.Element[]),
  };
}
