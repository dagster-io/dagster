import {RefetchQueriesFunction} from '@apollo/client';
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
  Tooltip,
} from '@dagster-io/ui-components';
import groupBy from 'lodash/groupBy';
import * as React from 'react';

import {useAssetGroupSelectorsForAssets} from './AssetGroupSuggest';
import {AssetWipeDialog} from './AssetWipeDialog';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetTableFragment} from './types/AssetTableFragment.types';
import {AssetViewType} from './useAssetView';
import {CloudOSSContext} from '../app/CloudOSSContext';
import {useUnscopedPermissions} from '../app/Permissions';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AssetGroupSelector, AssetKeyInput, ChangeReason} from '../graphql/types';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {testId} from '../testing/testId';
import {useFilters} from '../ui/Filters';
import {useAssetGroupFilter} from '../ui/Filters/useAssetGroupFilter';
import {useChangedFilter} from '../ui/Filters/useChangedFilter';
import {
  useAssetKindTagsForAssets,
  useComputeKindTagFilter,
} from '../ui/Filters/useComputeKindTagFilter';
import {FilterObject} from '../ui/Filters/useFilter';
import {VirtualizedAssetTable} from '../workspace/VirtualizedAssetTable';

type Asset = AssetTableFragment;

interface Props {
  view: AssetViewType;
  assets: Asset[];
  refreshState: QueryRefreshState;
  actionBarComponents: React.ReactNode;
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  requery?: RefetchQueriesFunction;
  searchPath: string;
  isFiltered: boolean;
  visibleAssetGroups: AssetGroupSelector[];
  setVisibleAssetGroups: (groups: AssetGroupSelector[]) => void;
  visibleComputeKindTags: string[];
  setVisibleComputeKindTags: (kindTags: string[]) => void;
  visibleChangedInBranch: ChangeReason[];
  setVisibleChangedInBranch: (changeReasons: ChangeReason[]) => void;
}

export const AssetTable = ({
  assets,
  actionBarComponents,
  refreshState,
  prefixPath,
  displayPathForAsset,
  requery,
  searchPath,
  isFiltered,
  view,
  visibleAssetGroups,
  setVisibleAssetGroups,
  visibleComputeKindTags,
  setVisibleComputeKindTags,
  visibleChangedInBranch,
  setVisibleChangedInBranch,
}: Props) => {
  const assetGroupOptions = useAssetGroupSelectorsForAssets(assets);
  const groupsFilter = useAssetGroupFilter({
    assetGroups: assetGroupOptions,
    visibleAssetGroups,
    setGroupFilters: setVisibleAssetGroups,
  });
  const changedInBranchFilter = useChangedFilter({
    changedInBranch: visibleChangedInBranch,
    setChangedInBranch: setVisibleChangedInBranch,
  });
  const allKindTags = useAssetKindTagsForAssets(assets);
  const computeKindFilter = useComputeKindTagFilter({
    allKindTags,
    computeKindTags: visibleComputeKindTags,
    setComputeKindTags: setVisibleComputeKindTags,
  });
  const filters: FilterObject[] = [groupsFilter, computeKindFilter];
  const {isBranchDeployment} = React.useContext(CloudOSSContext);
  if (isBranchDeployment) {
    filters.push(changedInBranchFilter);
  }
  const {button, activeFiltersJsx} = useFilters({
    filters,
  });
  const [toWipe, setToWipe] = React.useState<AssetKeyInput[] | undefined>();

  const groupedByDisplayKey = groupBy(assets, (a) => JSON.stringify(displayPathForAsset(a)));
  const displayKeys = Object.keys(groupedByDisplayKey).sort();

  const [{checkedIds: checkedDisplayKeys}, {onToggleFactory, onToggleAll}] =
    useSelectionReducer(displayKeys);

  const checkedAssets: Asset[] = [];
  displayKeys.forEach((displayKey) => {
    if (checkedDisplayKeys.has(displayKey)) {
      checkedAssets.push(...(groupedByDisplayKey[displayKey] || []));
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
        showRepoColumn
        view={view}
        onWipe={(assetKeys: AssetKeyInput[]) => setToWipe(assetKeys)}
      />
    );
  };

  return (
    <>
      <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
        <Box
          background={Colors.backgroundDefault()}
          flex={{alignItems: 'center', gap: 12}}
          padding={{vertical: 8, left: 24, right: 12}}
          style={{position: 'sticky', top: 0, zIndex: 1}}
        >
          {actionBarComponents}
          {button}
          <div style={{flex: 1}} />
          <QueryRefreshCountdown refreshState={refreshState} />
          <Box flex={{alignItems: 'center', gap: 8}}>
            {checkedAssets.some((c) => !c.definition) ? (
              <Tooltip content="One or more selected assets are not software-defined and cannot be launched directly.">
                <Button
                  intent="primary"
                  data-testid={testId('materialize-button')}
                  icon={<Icon name="materialization" />}
                  disabled
                >
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
        {activeFiltersJsx.length ? (
          <Box
            border="top-and-bottom"
            padding={12}
            flex={{direction: 'row', gap: 4, alignItems: 'center'}}
          >
            {activeFiltersJsx}
          </Box>
        ) : null}
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

  if (!canWipeAssets) {
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
          setShowBulkWipeDialog(false);
          clearSelection();
        }}
        requery={requery}
      />
    </>
  );
});
