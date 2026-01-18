import {Colors, Icon, MenuItem} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {DeleteDynamicPartitionsDialog} from './DeleteDynamicPartitionsDialog';
import {useAssetPermissions} from './useAssetPermissions';
import {CloudOSSContext} from '../app/CloudOSSContext';
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
        assetKeys={opts?.assetKey ? [opts.assetKey] : []}
        locationName={opts?.repoAddress.location || ''}
        onClick={() => setIsShowing(true)}
      />,
    ],
  };
};

type DeleteDynamicPartitionsMenuItemProps = {
  assetKeys: AssetKeyInput[];
  locationName: string;
  onClick: () => void;
};

const DeleteDynamicPartitionsMenuItem = ({
  assetKeys,
  locationName,
  onClick,
}: DeleteDynamicPartitionsMenuItemProps) => {
  // this separate comp exists to defer this expensive query until
  // the menuItem is rendered instead of when the hook is called
  const {hasWipePermission} = useAssetPermissions(assetKeys, locationName);

  return (
    <MenuItem
      text="Delete partitions"
      icon={<Icon name="delete" color={Colors.accentRed()} />}
      disabled={!hasWipePermission}
      intent="danger"
      onClick={onClick}
    />
  );
};
