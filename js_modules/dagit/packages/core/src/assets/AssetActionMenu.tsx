import {Button, Icon, Menu, MenuItem, Popover} from '@dagster-io/ui';
import * as React from 'react';

import {usePermissions} from '../app/Permissions';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableFragment} from './types/AssetTableFragment';

interface Props {
  repoAddress: RepoAddress | null;
  asset: AssetTableFragment;
  onWipe?: (assets: AssetTableFragment[]) => void;
}

export const AssetActionMenu: React.FC<Props> = (props) => {
  const {repoAddress, asset, onWipe} = props;
  const {canWipeAssets} = usePermissions();
  const {path} = asset.key;

  return (
    <Popover
      position="bottom-right"
      content={
        <Menu>
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
            disabled={!onWipe || !canWipeAssets.enabled}
            intent="danger"
            onClick={() => canWipeAssets.enabled && onWipe && onWipe([asset])}
          />
        </Menu>
      }
    >
      <Button icon={<Icon name="expand_more" />} />
    </Popover>
  );
};
