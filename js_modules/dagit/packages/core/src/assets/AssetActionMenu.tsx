import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissionsForLocation} from '../app/Permissions';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {useAssetLaunchAction} from './LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableFragment} from './types/AssetTableFragment.types';

interface Props {
  repoAddress: RepoAddress | null;
  asset: AssetTableFragment;
  onWipe?: (assets: AssetTableFragment[]) => void;
}

export const AssetActionMenu: React.FC<Props> = (props) => {
  const {repoAddress, asset, onWipe} = props;
  const {
    permissions: {canWipeAssets, canLaunchPipelineExecution},
  } = usePermissionsForLocation(repoAddress?.location);
  const {path} = asset.key;

  const {onClick, loading, launchpadElement} = useAssetLaunchAction({
    type: 'materialization',
  });

  return (
    <>
      <Popover
        position="bottom-right"
        content={
          <Menu>
            <Tooltip
              content={
                !canLaunchPipelineExecution
                  ? 'You do not have permission to materialize assets'
                  : 'Shift+click to add configuration'
              }
              placement="left"
              display="block"
              useDisabledButtonTooltipFix
            >
              <MenuItem
                text="Materialize"
                icon={loading ? <Spinner purpose="body-text" /> : 'materialization'}
                disabled={!canLaunchPipelineExecution || loading}
                onClick={(e) => onClick([asset.key], e)}
              />
            </Tooltip>
            <MenuLink
              text="Show in group"
              to={
                repoAddress && asset.definition?.groupName
                  ? workspacePathFromAddress(
                      repoAddress,
                      `/asset-groups/${asset.definition.groupName}`,
                    )
                  : ''
              }
              disabled={!asset?.definition}
              icon="asset_group"
            />
            <MenuLink
              text="View neighbors"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'neighbors'})}
              disabled={!asset?.definition}
              icon="graph_neighbors"
            />
            <MenuLink
              text="View upstream assets"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'upstream'})}
              disabled={!asset?.definition}
              icon="graph_upstream"
            />
            <MenuLink
              text="View downstream assets"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'downstream'})}
              disabled={!asset?.definition}
              icon="graph_downstream"
            />
            <MenuItem
              text="Wipe materializations"
              icon="delete"
              disabled={!onWipe || !canWipeAssets}
              intent="danger"
              onClick={() => canWipeAssets && onWipe && onWipe([asset])}
            />
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
      {launchpadElement}
    </>
  );
};
