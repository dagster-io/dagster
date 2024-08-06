import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {DeleteDynamicPartitionsDialog} from './DeleteDynamicPartitionsDialog';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {usePermissionsForLocation} from '../app/Permissions';

export function useDeleteDynamicPartitionsDialog(
  opts: {partitionsDefName: string; repository: {name: string; location: {name: string}}} | null,
  refresh: () => void,
) {
  const [showing, setShowing] = useState(false);
  const {
    permissions: {canWipeAssets},
  } = usePermissionsForLocation(opts ? opts.repository.location.name : null);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  return {
    element: opts ? (
      <DeleteDynamicPartitionsDialog
        partitionsDefName={opts.partitionsDefName}
        repository={opts.repository}
        isOpen={showing}
        onClose={() => setShowing(false)}
        onComplete={refresh}
      />
    ) : (
      <span />
    ),
    dropdownOptions: canSeeWipeMaterializationAction
      ? [
          <MenuItem
            key="delete"
            text="Delete dynamic partitions"
            icon={<Icon name="delete" color={Colors.accentRed()} />}
            disabled={!canWipeAssets}
            intent="danger"
            onClick={() => setShowing(true)}
          />,
        ]
      : ([] as JSX.Element[]),
  };
}
