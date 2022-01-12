import {gql, RefetchQueriesFunction} from '@apollo/client';
import {
  Box,
  ButtonWIP,
  Checkbox,
  IconWIP,
  markdownToPlaintext,
  MenuItemWIP,
  MenuWIP,
  Popover,
  Table,
} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {usePermissions} from '../app/Permissions';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {PipelineReference} from '../pipelines/PipelineReference';

import {AssetLink} from './AssetLink';
import {AssetWipeDialog} from './AssetWipeDialog';
import {AssetTableFragment as Asset} from './types/AssetTableFragment';

type AssetKey = {path: string[]};

export const AssetTable = ({
  assets,
  actionBarComponents,
  prefixPath,
  displayPathForAsset,
  maxDisplayCount,
  requery,
}: {
  actionBarComponents: React.ReactNode;
  assets: Asset[];
  prefixPath: string[];
  displayPathForAsset: (asset: Asset) => string[];
  maxDisplayCount?: number;
  requery?: RefetchQueriesFunction;
}) => {
  const [toWipe, setToWipe] = React.useState<AssetKey[] | undefined>();
  const {canWipeAssets} = usePermissions();
  const {flagAssetGraph} = useFeatureFlags();

  const pathMap: {[key: string]: Asset[]} = {};
  assets.forEach((asset) => {
    const path = displayPathForAsset(asset);
    const pathKey = JSON.stringify(path);
    pathMap[pathKey] = [...(pathMap[pathKey] || []), asset];
  });
  const [{checkedIds: checkedPaths}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    Object.keys(pathMap),
  );
  const sorted = Object.keys(pathMap)
    .sort()
    .slice(0, maxDisplayCount)
    .map((x) => JSON.parse(x));

  const checkedAssets = new Set<Asset>();
  sorted.forEach((path) => {
    const key = JSON.stringify(path);
    if (checkedPaths.has(key)) {
      const assets = pathMap[key] || [];
      assets.forEach((asset) => checkedAssets.add(asset));
    }
  });

  return (
    <Box flex={{direction: 'column'}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{vertical: 8, left: 24, right: 12}}>
        {actionBarComponents}
        <div style={{flex: 1}} />
        <AssetActions
          selected={Array.from(checkedAssets)}
          clearSelection={() => onToggleAll(false)}
        />
      </Box>
      <Table>
        <thead>
          <tr>
            {canWipeAssets ? (
              <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
                <Checkbox
                  indeterminate={checkedPaths.size > 0 && checkedPaths.size !== sorted.length}
                  checked={checkedPaths.size === sorted.length}
                  onChange={(e) => {
                    if (e.target instanceof HTMLInputElement) {
                      onToggleAll(checkedPaths.size !== sorted.length);
                    }
                  }}
                />
              </th>
            ) : null}
            <th>Asset Key</th>
            {flagAssetGraph ? <th>Description</th> : null}
            {flagAssetGraph ? <th style={{maxWidth: 250}}>Defined In</th> : null}
            {canWipeAssets ? <th style={{width: 80}}>Actions</th> : null}
          </tr>
        </thead>
        <tbody>
          {sorted.map((path, idx) => {
            const pathStr = JSON.stringify(path);
            return (
              <AssetEntryRow
                key={idx}
                prefixPath={prefixPath}
                path={path}
                assets={pathMap[pathStr] || []}
                shouldShowAssetGraphColumns={flagAssetGraph}
                isSelected={checkedPaths.has(pathStr)}
                onToggleChecked={onToggleFactory(pathStr)}
                onWipe={(assets: Asset[]) => setToWipe(assets.map((asset) => asset.key))}
                canWipe={canWipeAssets}
              />
            );
          })}
        </tbody>
      </Table>
      <AssetWipeDialog
        assetKeys={toWipe || []}
        isOpen={!!toWipe}
        onClose={() => setToWipe(undefined)}
        onComplete={() => setToWipe(undefined)}
        requery={requery}
      />
    </Box>
  );
};

const AssetEntryRow: React.FC<{
  prefixPath: string[];
  path: string[];
  isSelected: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  shouldShowAssetGraphColumns: boolean;
  assets: Asset[];
  onWipe: (assets: Asset[]) => void;
  canWipe: boolean;
}> = React.memo(
  ({
    prefixPath,
    path,
    shouldShowAssetGraphColumns,
    assets,
    isSelected,
    onToggleChecked,
    onWipe,
    canWipe,
  }) => {
    const fullPath = [...prefixPath, ...path];
    const isAssetEntry = assets.length === 1 && fullPath.join('/') === assets[0].key.path.join('/');
    const linkUrl = `/instance/assets/${fullPath.map(encodeURIComponent).join('/')}`;
    const first = assets[0];

    const onChange = (e: React.FormEvent<HTMLInputElement>) => {
      if (e.target instanceof HTMLInputElement) {
        const {checked} = e.target;
        const shiftKey =
          e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
        onToggleChecked({checked, shiftKey});
      }
    };
    return (
      <tr>
        {canWipe ? (
          <td style={{paddingRight: '4px'}}>
            <Checkbox checked={isSelected} onChange={onChange} />
          </td>
        ) : null}
        <td>
          <AssetLink path={path} url={linkUrl} trailingSlash={!isAssetEntry} />
        </td>
        {shouldShowAssetGraphColumns ? (
          <td>
            {first.definition &&
              first.definition.description &&
              markdownToPlaintext(first.definition.description).split('\n')[0]}
          </td>
        ) : null}
        {shouldShowAssetGraphColumns ? (
          <td>
            <Box flex={{direction: 'column', gap: 2}}>
              {(first.definition?.jobs || []).map((job) => (
                <PipelineReference
                  key={job.id}
                  isJob
                  showIcon
                  pipelineName={job.name}
                  pipelineHrefContext={{
                    name: job.repository.name,
                    location: job.repository.location.name,
                  }}
                />
              ))}
            </Box>
          </td>
        ) : null}
        {canWipe ? (
          <td>
            {isAssetEntry ? (
              <Popover
                content={
                  <MenuWIP>
                    <MenuItemWIP
                      text="Wipe…"
                      icon="delete"
                      intent="danger"
                      onClick={() => onWipe(assets)}
                    />
                  </MenuWIP>
                }
                position="bottom-right"
              >
                <ButtonWIP icon={<IconWIP name="expand_more" />} />
              </Popover>
            ) : null}
          </td>
        ) : null}
      </tr>
    );
  },
);

const AssetActions: React.FC<{
  selected: Asset[];
  clearSelection: () => void;
  requery?: RefetchQueriesFunction;
}> = React.memo(({selected, clearSelection, requery}) => {
  const [showBulkWipeDialog, setShowBulkWipeDialog] = React.useState<boolean>(false);
  const {canWipeAssets} = usePermissions();

  if (!canWipeAssets) {
    return null;
  }

  const disabled = selected.length === 0;
  const label =
    selected.length > 1
      ? `Wipe materializations for ${selected.length} assets`
      : selected.length === 1
      ? `Wipe materializations for 1 asset`
      : `Wipe materializations`;

  return (
    <>
      <ButtonWIP
        disabled={disabled}
        icon={<IconWIP name="delete" />}
        intent={disabled ? 'none' : 'danger'}
        outlined={!disabled}
        onClick={() => setShowBulkWipeDialog(true)}
      >
        {label}
      </ButtonWIP>
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

export const ASSET_TABLE_FRAGMENT = gql`
  fragment AssetTableFragment on Asset {
    __typename
    id
    key {
      path
    }
    definition {
      id
      opName
      description
      jobs {
        id
        name
        repository {
          id
          name
          location {
            id
            name
          }
        }
      }
    }
  }
`;
