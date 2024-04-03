import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {
  executionDisabledMessageForAssets,
  useMaterializationAction,
} from './LaunchAssetExecutionButton';
import {useObserveAction} from './LaunchAssetObservationButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {showSharedToaster} from '../app/DomUtils';
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

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  const {executeItem, launchpadElement} = useExecuteAssetMenuItem(path, definition);

  return (
    <>
      {launchpadElement}
      <Popover
        position="bottom-right"
        content={
          <Menu>
            {executeItem}

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
            {canSeeWipeMaterializationAction ? (
              <MenuItem
                text="Wipe materializations"
                icon="delete"
                disabled={!onWipe || !canWipeAssets}
                intent="danger"
                onClick={() => canWipeAssets && onWipe && onWipe([{path}])}
              />
            ) : null}
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
    </>
  );
};

export const useExecuteAssetMenuItem = (
  path: string[],
  definition: {
    isSource: boolean;
    isExecutable: boolean;
    hasMaterializePermission: boolean;
  } | null,
) => {
  const disabledMessage = definition
    ? executionDisabledMessageForAssets([definition])
    : 'Asset definition not found in a code location';

  const {
    featureContext: {canSeeMaterializeAction},
  } = useContext(CloudOSSContext);

  const materialize = useMaterializationAction();
  const observe = useObserveAction();

  if (!canSeeMaterializeAction) {
    return {executeItem: null, launchpadElement: null};
  }

  if (definition?.isExecutable && definition.isSource && definition.hasMaterializePermission) {
    return {
      launchpadElement: null,
      executeItem: (
        <MenuItem
          text="Observe"
          icon={observe.loading ? <Spinner purpose="body-text" /> : 'observation'}
          disabled={observe.loading}
          onClick={(e) => {
            void showSharedToaster({
              intent: 'primary',
              message: 'Initiating observation',
              icon: 'observation',
            });
            observe.onClick([{path}], e);
          }}
        />
      ),
    };
  }

  return {
    launchpadElement: materialize.launchpadElement,
    executeItem: (
      <Tooltip
        content={disabledMessage || 'Shift+click to add configuration'}
        placement="left"
        display="block"
        useDisabledButtonTooltipFix
      >
        <MenuItem
          text="Materialize"
          icon={materialize.loading ? <Spinner purpose="body-text" /> : 'materialization'}
          disabled={!!disabledMessage || materialize.loading}
          onClick={(e) => {
            if (!definition) {
              return;
            }
            void showSharedToaster({
              intent: 'primary',
              message: 'Initiating materialization',
              icon: 'materialization',
            });

            materialize.onClick([{path}], e);
          }}
        />
      </Tooltip>
    ),
  };
};
