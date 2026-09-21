import {MenuItem} from '@dagster-io/ui-components';
import {AssetWipeDialog} from '@shared/assets/AssetWipeDialog';
import React, {useContext, useMemo, useState} from 'react';

import {RefetchQueriesFunction} from '../apollo-client';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {PermissionsContext} from '../app/Permissions';

export const useWipeMaterializations = ({
  onComplete,
  selected,
  requery,
}: {
  onComplete?: () => void;
  selected: {
    key: {path: string[]};
    definitionHasWipePermission: boolean;
    locationName?: string | null;
  }[];
  requery?: RefetchQueriesFunction;
}) => {
  const [showWipeDialog, setShowWipeDialog] = useState(false);
  const {unscopedPermissions, locationPermissions} = React.useContext(PermissionsContext);

  const hasWipePermission = useMemo(() => {
    if (selected.length === 0) {
      return false;
    }
    // Deployment-wide permission grants access to all assets
    if (unscopedPermissions.canWipeAssets?.enabled) {
      return true;
    }
    return selected.every((a) => {
      // Location-scoped permission grants access to assets in that location
      if (a.locationName && locationPermissions[a.locationName]?.canWipeAssets?.enabled) {
        return true;
      }
      // Per-asset permission from the definition (owner-based)
      return !!a.definitionHasWipePermission;
    });
  }, [selected, unscopedPermissions, locationPermissions]);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  const menuItem = useMemo(() => {
    if (!canSeeWipeMaterializationAction) {
      return null;
    }
    return (
      <MenuItem
        text="Wipe materializations"
        icon="delete"
        intent="danger"
        disabled={!hasWipePermission}
        onClick={() => setShowWipeDialog(true)}
      />
    );
  }, [hasWipePermission, canSeeWipeMaterializationAction]);

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
