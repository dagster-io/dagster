import {RefetchQueriesFunction} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Icon,
  MenuItem,
  Menu,
  Popover,
  Tooltip,
  Checkbox,
  NonIdealState,
} from '@dagster-io/ui';
import * as React from 'react';

import {useUnscopedPermissions} from '../app/Permissions';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AssetGroupSelector, AssetTableFragmentFragment} from '../graphql/graphql';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {VirtualizedAssetTable} from '../workspace/VirtualizedAssetTable';

import {AssetWipeDialog} from './AssetWipeDialog';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetViewType} from './useAssetView';

type Asset = AssetTableFragmentFragment;
type AssetKey = {path: string[]};

interface Props {
  view: AssetViewType;
  assets: Asset[];
  refreshState: QueryRefreshState;
  actionBarComponents: React.ReactNode;
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  requery?: RefetchQueriesFunction;
  searchPath: string;
  searchGroup: AssetGroupSelector | null;
}

export const AssetTable: React.FC<Props> = ({
  assets,
  actionBarComponents,
  refreshState,
  prefixPath,
  displayPathForAsset,
  requery,
  searchPath,
  searchGroup,
  view,
}) => {
  const [toWipe, setToWipe] = React.useState<AssetKey[] | undefined>();

  const groupedByFirstComponent: {[pathComponent: string]: Asset[]} = {};

  assets.forEach((asset) => {
    const displayPathKey = JSON.stringify(displayPathForAsset(asset));
    groupedByFirstComponent[displayPathKey] = [
      ...(groupedByFirstComponent[displayPathKey] || []),
      asset,
    ];
  });

  const [{checkedIds: checkedPaths}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    Object.keys(groupedByFirstComponent),
  );

  const checkedAssets: Asset[] = [];
  const checkedPathsOnscreen: string[] = [];

  const pageDisplayPathKeys = Object.keys(groupedByFirstComponent).sort();
  pageDisplayPathKeys.forEach((pathKey) => {
    if (checkedPaths.has(pathKey)) {
      checkedPathsOnscreen.push(pathKey);
      checkedAssets.push(...(groupedByFirstComponent[pathKey] || []));
    }
  });

  const content = () => {
    if (!assets.length) {
      if (searchPath) {
        return (
          <Box padding={{top: 64}}>
            <NonIdealState
              icon="search"
              title="No matching assets"
              description={
                searchGroup ? (
                  <div>
                    No assets matching <strong>{searchPath}</strong> were found in{' '}
                    <strong>{searchGroup.groupName}</strong>
                  </div>
                ) : (
                  <div>
                    No assets matching <strong>{searchPath}</strong> were found
                  </div>
                )
              }
            />
          </Box>
        );
      }

      return (
        <Box padding={{top: 20}}>
          <NonIdealState
            icon="search"
            title="No assets"
            description={
              searchGroup ? (
                <div>
                  No assets were found in <strong>{searchGroup.groupName}</strong>
                </div>
              ) : (
                'No assets were found'
              )
            }
          />
        </Box>
      );
    }

    return (
      <VirtualizedAssetTable
        headerCheckbox={
          <Checkbox
            indeterminate={
              checkedPathsOnscreen.length > 0 &&
              checkedPathsOnscreen.length !== pageDisplayPathKeys.length
            }
            checked={
              checkedPathsOnscreen.length > 0 &&
              checkedPathsOnscreen.length === pageDisplayPathKeys.length
            }
            onChange={(e) => {
              if (e.target instanceof HTMLInputElement) {
                onToggleAll(checkedPathsOnscreen.length !== pageDisplayPathKeys.length);
              }
            }}
          />
        }
        prefixPath={prefixPath}
        groups={groupedByFirstComponent}
        checkedPaths={checkedPaths}
        onToggleFactory={onToggleFactory}
        showRepoColumn
        view={view}
        onWipe={(assets: Asset[]) => setToWipe(assets.map((asset) => asset.key))}
      />
    );
  };

  return (
    <>
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <Box
          background={Colors.White}
          flex={{alignItems: 'center', gap: 12}}
          padding={{vertical: 8, left: 24, right: 12}}
          style={{position: 'sticky', top: 0, zIndex: 1}}
        >
          {actionBarComponents}
          <div style={{flex: 1}} />
          <QueryRefreshCountdown refreshState={refreshState} />
          <Box flex={{alignItems: 'center', gap: 8}}>
            {checkedAssets.some((c) => !c.definition) ? (
              <Tooltip content="One or more selected assets are not software-defined and cannot be launched directly.">
                <Button intent="primary" icon={<Icon name="materialization" />} disabled>
                  {checkedAssets.length > 1
                    ? `Materialize (${checkedAssets.length.toLocaleString()})`
                    : 'Materialize'}
                </Button>
              </Tooltip>
            ) : (
              <LaunchAssetExecutionButton
                scope={{selected: checkedAssets.map((a) => ({...a.definition!, assetKey: a.key}))}}
              />
            )}
            <MoreActionsDropdown
              selected={checkedAssets}
              clearSelection={() => onToggleAll(false)}
            />
          </Box>
        </Box>
        {content()}
      </Box>
      <AssetWipeDialog
        assetKeys={toWipe || []}
        isOpen={!!toWipe}
        onClose={() => setToWipe(undefined)}
        onComplete={() => setToWipe(undefined)}
        requery={requery}
      />
    </>
  );
};

const MoreActionsDropdown: React.FC<{
  selected: Asset[];
  clearSelection: () => void;
  requery?: RefetchQueriesFunction;
}> = React.memo(({selected, clearSelection, requery}) => {
  const [showBulkWipeDialog, setShowBulkWipeDialog] = React.useState<boolean>(false);
  const {canWipeAssets} = useUnscopedPermissions();

  if (!canWipeAssets.enabled) {
    return null;
  }

  const disabled = selected.length === 0;

  return (
    <>
      <Popover
        position="bottom-right"
        content={
          <Menu>
            <MenuItem
              text="Wipe materializations"
              onClick={() => setShowBulkWipeDialog(true)}
              icon={<Icon name="delete" color={disabled ? Colors.Gray600 : Colors.Red500} />}
              disabled={disabled}
              intent="danger"
            />
          </Menu>
        }
      >
        <Button icon={<Icon name="expand_more" />} />
      </Popover>
      <AssetWipeDialog
        assetKeys={selected.map((asset) => asset.key)}
        isOpen={showBulkWipeDialog}
        onClose={() => setShowBulkWipeDialog(false)}
        onComplete={() => {
          setShowBulkWipeDialog(false);
          clearSelection();
        }}
        requery={requery}
      />
    </>
  );
});
