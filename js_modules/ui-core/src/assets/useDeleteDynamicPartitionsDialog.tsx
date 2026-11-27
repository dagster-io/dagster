import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {DeleteDynamicPartitionsDialog} from './DeleteDynamicPartitionsDialog';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput, PartitionDefinitionType} from '../graphql/types';
import {RepoAddress} from '../workspace/types';

export const useDeleteDynamicPartitionsDialog = (
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
) => {
  const [isShowing, setIsShowing] = useState(false);

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
      element: undefined,
      dropdownOptions: [],
    };
  }

  return {
    element: (
      <DeleteDynamicPartitionsDialog
        repoAddress={opts.repoAddress}
        assetKey={opts.assetKey}
        partitionsDefName={dynamicDimension.dynamicPartitionsDefinitionName}
        isOpen={isShowing}
        onClose={() => setIsShowing(false)}
        onComplete={refresh}
      />
    ),
    dropdownOptions: [
      <DeleteDynamicPartitionsMenuItem
        key="delete"
        locationName={opts.repoAddress.location}
        onClick={() => setIsShowing(true)}
      />,
    ],
  };
};

type DeleteDynamicPartitionsMenuItemProps = {
  locationName: string;
  onClick: () => void;
};

const DeleteDynamicPartitionsMenuItem = ({
  locationName,
  onClick,
}: DeleteDynamicPartitionsMenuItemProps) => {
  // The backend checks edit_dynamic_partitions for the code location, not per asset. Wipe
  // permission only matters if the user opts to wipe materializations, which the dialog checks.
  const {
    permissions: {canEditDynamicPartitions},
  } = usePermissionsForLocation(locationName);

  return (
    <MenuItem
      text="Delete partitions"
      icon={<Icon name="delete" color={Colors.accentRed()} />}
      disabled={!canEditDynamicPartitions}
      intent="danger"
      onClick={onClick}
    />
  );
};
