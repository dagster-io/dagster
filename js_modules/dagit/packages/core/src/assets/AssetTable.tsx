import {gql, RefetchQueriesFunction} from '@apollo/client';
import {
  Box,
  ButtonWIP,
  Checkbox,
  ColorsWIP,
  IconWIP,
  markdownToPlaintext,
  MenuItemWIP,
  MenuLink,
  MenuWIP,
  Popover,
  Table,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {tokenForAssetKey} from '../app/Util';
import {useSelectionReducer} from '../hooks/useSelectionReducer';
import {RepositoryLink} from '../nav/RepositoryLink';
import {instanceAssetsExplorerPathToURL} from '../pipelines/PipelinePathUtils';

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

  const assetGroups: {[key: string]: Asset[]} = {};
  const checkedAssets: Asset[] = [];

  assets.forEach((asset) => {
    const displayPathKey = JSON.stringify(displayPathForAsset(asset));
    assetGroups[displayPathKey] = [...(assetGroups[displayPathKey] || []), asset];
  });

  const [{checkedIds: checkedPaths}, {onToggleFactory, onToggleAll}] = useSelectionReducer(
    Object.keys(assetGroups),
  );

  const pageDisplayPathKeys = Object.keys(assetGroups).sort().slice(0, maxDisplayCount);
  pageDisplayPathKeys.forEach((path) => {
    const key = JSON.stringify(path);
    if (checkedPaths.has(key)) {
      checkedAssets.push(...(assetGroups[key] || []));
    }
  });

  return (
    <Box flex={{direction: 'column'}}>
      <Box flex={{alignItems: 'center', gap: 12}} padding={{vertical: 8, left: 24, right: 12}}>
        {actionBarComponents}
        <div style={{flex: 1}} />
        <AssetBulkActions
          selected={Array.from(checkedAssets)}
          clearSelection={() => onToggleAll(false)}
        />
      </Box>
      <Table>
        <thead>
          <tr>
            <th style={{width: 42, paddingTop: 0, paddingBottom: 0}}>
              <Checkbox
                indeterminate={
                  checkedPaths.size > 0 && checkedPaths.size !== pageDisplayPathKeys.length
                }
                checked={checkedPaths.size === pageDisplayPathKeys.length}
                onChange={(e) => {
                  if (e.target instanceof HTMLInputElement) {
                    onToggleAll(checkedPaths.size !== pageDisplayPathKeys.length);
                  }
                }}
              />
            </th>
            <th>Asset Key</th>
            <th style={{width: 340}}>Defined In</th>
            <th style={{width: 80}}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {pageDisplayPathKeys.map((pathStr, idx) => {
            return (
              <AssetEntryRow
                key={idx}
                prefixPath={prefixPath}
                path={JSON.parse(pathStr)}
                assets={assetGroups[pathStr] || []}
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
  assets: Asset[];
  onWipe: (assets: Asset[]) => void;
  canWipe?: boolean;
}> = React.memo(({prefixPath, path, assets, isSelected, onToggleChecked, onWipe, canWipe}) => {
  const fullPath = [...prefixPath, ...path];
  const representsSingleAsset =
    assets.length === 1 && fullPath.join('/') === assets[0].key.path.join('/');
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
      <td style={{paddingRight: '4px'}}>
        <Checkbox checked={isSelected} onChange={onChange} />
      </td>
      <td>
        <AssetLink path={path} url={linkUrl} trailingSlash={!representsSingleAsset} />
        <Description>
          {first.definition &&
            first.definition.description &&
            markdownToPlaintext(first.definition.description).split('\n')[0]}
        </Description>
      </td>
      <td>
        {first.definition && (
          <Box flex={{direction: 'column', gap: 2}}>
            <RepositoryLink
              showIcon
              showRefresh={false}
              repoAddress={{
                name: first.definition.repository.name,
                location: first.definition.repository.location.name,
              }}
            />
          </Box>
        )}
      </td>
      <td style={{display: 'flex', alignItems: 'center', gap: 8}}>
        <Link
          to={instanceAssetsExplorerPathToURL({
            opsQuery: `++"${tokenForAssetKey({path})}"++`,
            opNames: [tokenForAssetKey({path})],
          })}
        >
          <ButtonWIP disabled={!representsSingleAsset || !first.definition?.opName}>
            View in Asset Graph
          </ButtonWIP>
        </Link>
        <Popover
          position="bottom-right"
          content={
            <MenuWIP>
              <MenuLink
                text="View details…"
                to={`/instance/assets/${path.join('/')}`}
                icon="view_list"
              />
              {representsSingleAsset && (
                <MenuItemWIP
                  text="Wipe Asset…"
                  icon="delete"
                  disabled={!canWipe}
                  intent="danger"
                  onClick={() => canWipe && onWipe(assets)}
                />
              )}
              {representsSingleAsset && (
                <MenuItemWIP
                  text="Wipe Asset…"
                  icon="delete"
                  disabled={!canWipe}
                  intent="danger"
                  onClick={() => canWipe && onWipe(assets)}
                />
              )}
            </MenuWIP>
          }
        >
          <ButtonWIP icon={<IconWIP name="expand_more" />} />
        </Popover>
      </td>
    </tr>
  );
});

const AssetBulkActions: React.FC<{
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
`;

const Description = styled.div`
  color: ${ColorsWIP.Gray800};
  font-size: 14px;
`;
