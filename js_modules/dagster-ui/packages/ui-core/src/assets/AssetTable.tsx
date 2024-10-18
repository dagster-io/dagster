import {
  Box,
  Button,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import * as React from 'react';
import {useContext, useMemo} from 'react';
import {AssetWipeDialog} from 'shared/assets/AssetWipeDialog.oss';

import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {AssetViewType} from './useAssetView';
import {RefetchQueriesFunction} from '../apollo-client';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {useUnscopedPermissions} from '../app/Permissions';
import {QueryRefreshCountdown, RefreshState} from '../app/QueryRefresh';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {StaticSetFilter} from '../ui/BaseFilters/useStaticSetFilter';
import {VirtualizedAssetTable} from '../workspace/VirtualizedAssetTable';

type Asset = AssetTableFragment;

type AssetWithDefinition = AssetTableFragment & {
  definition: NonNullable<AssetTableFragment['definition']>;
};

interface Props {
  view: AssetViewType;
  assets: Asset[];
  refreshState: RefreshState;
  actionBarComponents: React.ReactNode;
  belowActionBarComponents: React.ReactNode;
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  searchPath: string;
  isFiltered: boolean;
  kindFilter?: StaticSetFilter<string>;
  isLoading: boolean;
}

export const AssetTable = ({
  assets,
  actionBarComponents,
  belowActionBarComponents,
  refreshState,
  prefixPath,
  displayPathForAsset,
  searchPath,
  isFiltered,
  view,
  kindFilter,
  isLoading,
}: Props) => {
  const groupedByDisplayKey = useMemo(
    () => groupBy(assets, (a) => JSON.stringify(displayPathForAsset(a))),
    [assets, displayPathForAsset],
  );
  const displayKeys = useMemo(() => Object.keys(groupedByDisplayKey).sort(), [groupedByDisplayKey]);

  const [{checkedIds: checkedDisplayKeys}, {onToggleFactory, onToggleAll}] =
    useSelectionReducer(displayKeys);

  const checkedAssets = useMemo(() => {
    const assets: Asset[] = [];
    displayKeys.forEach((displayKey) => {
      if (checkedDisplayKeys.has(displayKey)) {
        groupedByDisplayKey[displayKey]?.forEach((asset) => {
          assets.push(asset);
        });
      }
    });
    return assets;
  }, [checkedDisplayKeys, displayKeys, groupedByDisplayKey]);

  const content = () => {
    if (!assets.length) {
      if (searchPath) {
        return (
          <Box padding={{top: 64}}>
            <NonIdealState
              icon="search"
              title="No matching assets"
              description={
                isFiltered ? (
                  <div>
                    No assets matching <strong>{searchPath}</strong> were found in the selected
                    filters
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
              isFiltered
                ? 'No assets were found matching the selected filters'
                : 'No assets were found'
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
              checkedDisplayKeys.size > 0 && checkedDisplayKeys.size !== displayKeys.length
            }
            checked={checkedDisplayKeys.size > 0 && checkedDisplayKeys.size === displayKeys.length}
            onChange={(e) => {
              if (e.target instanceof HTMLInputElement) {
                onToggleAll(checkedDisplayKeys.size !== displayKeys.length);
              }
            }}
          />
        }
        prefixPath={prefixPath}
        groups={groupedByDisplayKey}
        checkedDisplayKeys={checkedDisplayKeys}
        onToggleFactory={onToggleFactory}
        onRefresh={() => refreshState.refetch()}
        showRepoColumn
        view={view}
        kindFilter={kindFilter}
        isLoading={isLoading}
      />
    );
  };

  return (
    <>
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <Box
          background={Colors.backgroundDefault()}
          flex={{alignItems: 'center', gap: 12}}
          padding={{vertical: 12, horizontal: 24}}
          style={{position: 'sticky', top: 0, zIndex: 1}}
        >
          {actionBarComponents}
          <div style={{flex: 1}} />
          <QueryRefreshCountdown refreshState={refreshState} />
          <Box flex={{alignItems: 'center', gap: 8}}>
            <LaunchAssetExecutionButton
              scope={{
                selected: checkedAssets
                  .filter((a): a is AssetWithDefinition => !!a.definition)
                  .map((a) => ({...a.definition, assetKey: a.key})),
              }}
            />
            <MoreActionsDropdown
              selected={checkedAssets}
              clearSelection={() => onToggleAll(false)}
            />
          </Box>
        </Box>
        {belowActionBarComponents}
        {content()}
      </Box>
    </>
  );
};

interface MoreActionsDropdownProps {
  selected: Asset[];
  clearSelection: () => void;
  requery?: RefetchQueriesFunction;
}

const MoreActionsDropdown = React.memo((props: MoreActionsDropdownProps) => {
  const {selected, clearSelection, requery} = props;
  const [showBulkWipeDialog, setShowBulkWipeDialog] = React.useState<boolean>(false);
  const {
    permissions: {canWipeAssets},
  } = useUnscopedPermissions();

  const {
    featureContext: {canSeeWipeMaterializationAction},
  } = useContext(CloudOSSContext);

  if (!canWipeAssets || !canSeeWipeMaterializationAction) {
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
              icon={
                <Icon name="delete" color={disabled ? Colors.textDisabled() : Colors.accentRed()} />
              }
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
          clearSelection();
        }}
        requery={requery}
      />
    </>
  );
});
