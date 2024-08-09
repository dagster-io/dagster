import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {DeleteDynamicPartitionsDialog} from './DeleteDynamicPartitionsDialog';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput, PartitionDefinitionType} from '../graphql/types';
import {RepoAddress} from '../workspace/types';

export function useDeleteDynamicPartitionsDialog(
  opts: {
    repoAddress: RepoAddress;
    assetKey: AssetKeyInput;
    definition: {
      partitionDefinition: {
        dimensionTypes:
          | {type: PartitionDefinitionType; dynamicPartitionsDefinitionName: string | null}[]
          | null;
      } | null;
    };
  } | null,
  refresh?: () => void,
) {
  const [showing, setShowing] = useState(false);
  const {
    permissions: {canWipeAssets},
  } = usePermissionsForLocation(opts ? opts.repoAddress.location : null);

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  const dynamicDimension = opts?.definition.partitionDefinition?.dimensionTypes?.find(
    (d) => d.type === PartitionDefinitionType.DYNAMIC,
  );

  if (
    !opts ||
    !dynamicDimension?.dynamicPartitionsDefinitionName ||
    !canSeeWipeMaterializationAction
  ) {
    return {
      element: <span />,
      dropdownOptions: [] as JSX.Element[],
    };
  }

  return {
    element: (
      <DeleteDynamicPartitionsDialog
        repoAddress={opts.repoAddress}
        assetKey={opts.assetKey}
        partitionsDefName={dynamicDimension.dynamicPartitionsDefinitionName}
        isOpen={showing}
        onClose={() => setShowing(false)}
        onComplete={refresh}
      />
    ),
    dropdownOptions: [
      <MenuItem
        key="delete"
        text="Delete partitions"
        icon={<Icon name="delete" color={Colors.accentRed()} />}
        disabled={!canWipeAssets}
        intent="danger"
        onClick={() => setShowing(true)}
      />,
    ],
  };
}
