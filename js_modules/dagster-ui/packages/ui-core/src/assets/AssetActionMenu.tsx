import {Button, Icon, Menu, MenuItem, Popover, Spinner, Tooltip} from '@dagster-io/ui-components';
import {useContext, useMemo} from 'react';

import {optionsForExecuteButton, useMaterializationAction} from './LaunchAssetExecutionButton';
import {assetDetailsPathForKey} from './assetDetailsPathForKey';
import {AssetTableDefinitionFragment} from './types/AssetTableFragment.types';
import {useDeleteDynamicPartitionsDialog} from './useDeleteDynamicPartitionsDialog';
import {useObserveAction} from './useObserveAction';
import {useReportEventsModal} from './useReportEventsModal';
import {useWipeModal} from './useWipeModal';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {showSharedToaster} from '../app/DomUtils';
import {AssetKeyInput} from '../graphql/types';
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

  // Because the asset catalog loads a list of keys, and then definitions for SDAs,
  // we don't re-fetch the key inside the definition of each asset. Re-attach the
  // assetKey to the definition for the hook below.
  const asset = useMemo(
    () =>
      definition
        ? {...definition, isPartitioned: !!definition?.partitionDefinition, assetKey: {path}}
        : null,
    [path, definition],
  );
  const {executeItem, launchpadElement} = useExecuteAssetMenuItem(asset);

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
  definition: {
    assetKey: AssetKeyInput;
    isObservable: boolean;
    isExecutable: boolean;
    isPartitioned: boolean;
    hasMaterializePermission: boolean;
  } | null,
) => {
  const {materializeOption, observeOption} = optionsForExecuteButton(
    definition ? [definition] : [],
    {skipAllTerm: true},
  );

  const {
    featureContext: {canSeeMaterializeAction},
  } = useContext(CloudOSSContext);

  const materialize = useMaterializationAction();
  const observe = useObserveAction();
  const loading = materialize.loading || observe.loading;

  const [option, action] =
    materializeOption.disabledReason && !observeOption.disabledReason
      ? [observeOption, observe.onClick]
      : [materializeOption, materialize.onClick];

  const disabledMessage = definition
    ? option.disabledReason
    : 'Asset definition not found in a code location';

  if (!canSeeMaterializeAction) {
    return {executeItem: null, launchpadElement: null};
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
          text={option.label}
          icon={loading ? <Spinner purpose="body-text" /> : option.icon}
          disabled={!!disabledMessage || loading}
          onClick={(e) => {
            if (!definition) {
              return;
            }
            void showSharedToaster({
              intent: 'primary',
              message: `Initiating...`,
            });

            action([definition.assetKey], e);
          }}
        />
      </Tooltip>
    ),
  };
};
