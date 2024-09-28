import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useContext} from 'react';

import {
  executionDisabledMessageForAssets,
  useMaterializationAction,
} from './LaunchAssetExecutionButton';
import {useObserveAction} from './LaunchAssetObservationButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {useDeleteDynamicPartitionsDialog} from './useDeleteDynamicPartitionsDialog';
import {useReportEventsModal} from './useReportEventsModal';
import {useWipeModal} from './useWipeModal';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {showSharedToaster} from '../app/DomUtils';
import {MenuLink} from '../ui/MenuLink';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  path: string[];
  definition: AssetTableDefinitionFragment | null;
  repoAddress: RepoAddress | null;
  onRefresh?: () => void;
}

export const AssetActionMenu = (props: Props) => {
  const {repoAddress, path, definition, onRefresh} = props;
  const {
    featureContext: {canSeeMaterializeAction},
  } = useContext(CloudOSSContext);

  const {executeItem, launchpadElement} = useExecuteAssetMenuItem(path, definition);

  const deletePartitions = useDeleteDynamicPartitionsDialog(
    repoAddress && definition ? {repoAddress, assetKey: {path}, definition} : null,
    onRefresh,
  );

  const wipe = useWipeModal(
    repoAddress && definition ? {repository: definition.repository, assetKey: {path}} : null,
    onRefresh,
  );

  const reportEvents = useReportEventsModal(
    repoAddress
      ? {
          assetKey: {path},
          isPartitioned: !!definition?.partitionDefinition,
          repoAddress,
          hasReportRunlessAssetEventPermission: !!definition?.hasReportRunlessAssetEventPermission,
        }
      : null,
  );
  return (
    <>
      {launchpadElement}
      {wipe.element}
      {reportEvents.element}
      {deletePartitions.element}
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
              text="View checks"
              to={assetDetailsPathForKey({path}, {view: 'checks'})}
              disabled={!definition}
              icon="asset_check"
            />
            <MenuLink
              text="View lineage"
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
            {canSeeMaterializeAction && definition?.hasMaterializePermission
              ? reportEvents.dropdownOptions.map((option) => (
                  <MenuItem
                    key={option.label}
                    text={option.label}
                    icon={option.icon}
                    onClick={option.onClick}
                  />
                ))
              : undefined}
            {wipe.dropdownOptions}
            {deletePartitions.dropdownOptions}
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
    isObservable: boolean;
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

  if (definition?.isExecutable && definition.isObservable && definition.hasMaterializePermission) {
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
