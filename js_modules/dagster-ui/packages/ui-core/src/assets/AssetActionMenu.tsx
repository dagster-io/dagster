import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';

import {
  executionDisabledMessageForAssets,
  useMaterializationAction,
} from './LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {usePermissionsForLocation} from '../app/Permissions';
import {AssetKeyInput} from '../graphql/types';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  path: string[];
  definition: AssetTableDefinitionFragment | null;
  repoAddress: RepoAddress | null;
  onWipe?: (assets: AssetKeyInput[]) => void;
}

export const AssetActionMenu = (props: Props) => {
  const {repoAddress, path, definition, onWipe} = props;
  const {
    permissions: {canWipeAssets},
  } = usePermissionsForLocation(repoAddress?.location);

  const {onClick, loading, launchpadElement} = useMaterializationAction();
  const disabledMessage = definition
    ? executionDisabledMessageForAssets([definition])
    : 'Asset definition not found in a code location';

  return (
    <>
      <Popover
        position="bottom-right"
        content={
          <Menu>
            <Tooltip
              content={disabledMessage || 'Shift+click to add configuration'}
              placement="left"
              display="block"
              useDisabledButtonTooltipFix
            >
              <MenuItem
                text="Materialize"
                icon={loading ? <Spinner purpose="body-text" /> : 'materialization'}
                disabled={!!disabledMessage || loading}
                onClick={(e) => onClick([{path}], e)}
              />
            </Tooltip>
            <MenuLink
              text="Show in group"
              to={
                repoAddress && definition?.groupName
                  ? workspacePathFromAddress(repoAddress, `/asset-groups/${definition.groupName}`)
                  : ''
              }
              disabled={!definition}
              icon="asset_group"
            />
            <MenuLink
              text="View neighbors"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'neighbors'})}
              disabled={!definition}
              icon="graph_neighbors"
            />
            <MenuLink
              text="View upstream assets"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'upstream'})}
              disabled={!definition}
              icon="graph_upstream"
            />
            <MenuLink
              text="View downstream assets"
              to={assetDetailsPathForKey({path}, {view: 'lineage', lineageScope: 'downstream'})}
              disabled={!definition}
              icon="graph_downstream"
            />
            <MenuItem
              text="Wipe materializations"
              icon="delete"
              disabled={!onWipe || !canWipeAssets}
              intent="danger"
              onClick={() => canWipeAssets && onWipe && onWipe([{path}])}
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
