import {MenuItem} from '@dagster-io/ui-components';
import {AssetWipeDialog} from '@shared/assets/AssetWipeDialog';
import {useContext, useMemo, useState} from 'react';

import {RefetchQueriesFunction} from '../apollo-client';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {useUnscopedPermissions} from '../app/Permissions';

export const useWipeMaterializations = ({
  onComplete,
  selected,
  requery,
}: {
  onComplete?: () => void;
  selected: {key: {path: string[]}}[];
  requery?: RefetchQueriesFunction;
}) => {
  const [showWipeDialog, setShowWipeDialog] = useState(false);
  const {
    permissions: {canWipeAssets},
  } = useUnscopedPermissions();

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  const menuItem = useMemo(() => {
    if (!canWipeAssets || !canSeeWipeMaterializationAction) {
      return null;
    }
    return (
      <MenuItem
        text="Wipe materializations"
        icon="delete"
        intent="danger"
        onClick={() => setShowWipeDialog(true)}
      />
    );
  }, [canWipeAssets, canSeeWipeMaterializationAction]);

  return {
    menuItem,
    dialog: (
      <AssetWipeDialog
        assetKeys={selected.map((asset) => asset.key)}
        isOpen={showWipeDialog}
        onClose={() => setShowWipeDialog(false)}
        onComplete={onComplete}
        requery={requery}
      />
    ),
  };
};
