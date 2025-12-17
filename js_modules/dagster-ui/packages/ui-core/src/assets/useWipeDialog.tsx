import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {Dispatch, SetStateAction, useContext, useState} from 'react';
import {AssetWipeDialog} from 'shared/assets/AssetWipeDialog.oss';

import {useAssetPermissions} from './useAssetPermissions';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {AssetKeyInput} from '../graphql/types';

export const useWipeDialog = (
  opts: {assetKey: AssetKeyInput; repository: {location: {name: string}} | null} | null,
  refresh?: VoidFunction,
) => {
  const [isShowing, setIsShowing] = useState(false);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

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
            <WipeDialogMenuItem
              key="wipe"
              setIsShowing={setIsShowing}
              assetKeys={opts?.assetKey ? [opts.assetKey] : []}
              locationName={opts?.repository?.location.name || ''}
            />,
          ]
        : [],
  };
};

type WipeDialogMenuItemProps = {
  assetKeys: AssetKeyInput[];
  locationName: string;
  setIsShowing: Dispatch<SetStateAction<boolean>>;
};

const WipeDialogMenuItem = ({assetKeys, locationName, setIsShowing}: WipeDialogMenuItemProps) => {
  // this separate comp exists to defer this expensive query until
  // the menuItem is rendered instead of when the hook is called
  const {hasWipePermission} = useAssetPermissions(assetKeys, locationName);

  return (
    <MenuItem
      text="Wipe materializations"
      icon={<Icon name="delete" color={Colors.accentRed()} />}
      disabled={!hasWipePermission}
      intent="danger"
      onClick={() => setIsShowing(true)}
    />
  );
};
