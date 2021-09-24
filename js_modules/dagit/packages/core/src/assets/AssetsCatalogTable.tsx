import {gql, useQuery} from '@apollo/client';
import {
  Button,
  Checkbox,
  Menu,
  MenuItem,
  Popover,
  InputGroup as BlueprintInputGroup,
  NonIdealState,
  Colors,
  ButtonGroup,
} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePermissions} from '../app/Permissions';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Loading} from '../ui/Loading';
import {Table} from '../ui/Table';
import {Tag} from '../ui/Tag';

import {AssetWipeDialog} from './AssetWipeDialog';
import {AssetsFilter, filterAssets} from './AssetsFilter';
import {
  AssetsTableQuery,
  AssetsTableQuery_assetsOrError_AssetConnection_nodes,
  AssetsTableQuery_assetsOrError_AssetConnection_nodes_key,
  AssetsTableQuery_assetsOrError_AssetConnection_nodes_tags,
} from './types/AssetsTableQuery';
import {useAssetView} from './useAssetView';

type Asset = AssetsTableQuery_assetsOrError_AssetConnection_nodes;
type AssetKey = AssetsTableQuery_assetsOrError_AssetConnection_nodes_key;
type AssetTag = AssetsTableQuery_assetsOrError_AssetConnection_nodes_tags;

const EXPERIMENTAL_TAGS_WARNING = (
  <Box style={{maxWidth: 300}}>
    Tags are an experimental feature of asset materializations. See the{' '}
    <a
      href="https://docs.dagster.io/_apidocs/solids#dagster.AssetMaterialization"
      style={{color: Colors.WHITE}}
    >
      AssetMaterialization documentation
    </a>{' '}
    for more about adding asset tags.
  </Box>
);

const POLL_INTERVAL = 15000;

export const AssetsCatalogTable: React.FC<{prefixPath?: string[]}> = ({prefixPath}) => {
  const queryResult = useQuery<AssetsTableQuery>(ASSETS_TABLE_QUERY, {
    notifyOnNetworkStatusChange: true,
    pollInterval: POLL_INTERVAL,
  });

  const [q, setQ] = React.useState<string>('');
  const [view, setView] = useAssetView();

  const isFlattened = view !== 'directory';
  const history = useHistory();
  const setIsFlattened = (flat: boolean) => {
    setView(flat ? 'flat' : 'directory');
    if (flat && prefixPath) {
      history.push('/instance/assets');
    }
  };

  return (
    <div style={{flexGrow: 1}}>
      <Loading allowStaleData queryResult={queryResult}>
        {({assetsOrError}) => {
          if (assetsOrError.__typename === 'PythonError') {
            return (
              <Wrapper>
                <PythonErrorInfo error={assetsOrError} />
              </Wrapper>
            );
          }

          const allAssets = assetsOrError.nodes;
          const assets = prefixPath
            ? assetsOrError.nodes.filter(
                (asset: Asset) =>
                  prefixPath.length < asset.key.path.length &&
                  prefixPath.every((part: string, i: number) => part === asset.key.path[i]),
              )
            : assetsOrError.nodes;

          const matching = isFlattened
            ? filterAssets(assets, q)
            : assets.filter((asset) => !q || matches(asset.key.path.join('/'), q));

          if (!assets.length) {
            return (
              <Wrapper>
                <NonIdealState
                  icon="panel-table"
                  title="Assets"
                  description={
                    <p>
                      {prefixPath && prefixPath.length ? (
                        <span>
                          There are no matching materialized assets with the specified asset key.
                        </span>
                      ) : (
                        <span>There are no known materialized assets.</span>
                      )}
                      Any asset keys that have been specified with an{' '}
                      <code>AssetMaterialization</code> during a pipeline run will appear here. See
                      the{' '}
                      <a href="https://docs.dagster.io/_apidocs/solids#dagster.AssetMaterialization">
                        AssetMaterialization documentation
                      </a>{' '}
                      for more information.
                    </p>
                  }
                />
              </Wrapper>
            );
          }

          const showSwitcher = prefixPath || assets.some((asset) => asset.key.path.length > 1);
          return (
            <Wrapper>
              <Box flex={{justifyContent: 'space-between'}}>
                <div>
                  {showSwitcher ? (
                    <Group spacing={8} direction="row">
                      <ButtonGroup>
                        <Button
                          icon="list"
                          title="Flat"
                          active={isFlattened}
                          onClick={() => setIsFlattened(true)}
                        />
                        <Button
                          icon="folder-close"
                          title="Directory"
                          active={!isFlattened}
                          onClick={() => setIsFlattened(false)}
                        />
                      </ButtonGroup>
                      {isFlattened ? (
                        <AssetsFilter assets={assets} query={q} onSetQuery={setQ} />
                      ) : (
                        <AssetSearch assets={allAssets} />
                      )}
                    </Group>
                  ) : isFlattened ? (
                    <AssetsFilter assets={assets} query={q} onSetQuery={setQ} />
                  ) : (
                    <AssetSearch assets={allAssets} />
                  )}
                </div>
                <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
              </Box>
              <AssetsTable
                assets={matching}
                currentPath={prefixPath || []}
                setQuery={setQ}
                isFlattened={isFlattened}
              />
            </Wrapper>
          );
        }}
      </Loading>
    </div>
  );
};

const matches = (haystack: string, needle: string) =>
  needle
    .toLowerCase()
    .split(' ')
    .filter((x) => x)
    .every((word) => haystack.toLowerCase().includes(word));

const AssetSearch = ({assets}: {assets: Asset[]}) => {
  const history = useHistory();
  const [open, setOpen] = React.useState(false);
  const [highlight, setHighlight] = React.useState<number>(0);
  const [q, setQ] = React.useState<string>('');

  React.useEffect(() => {
    setHighlight(0);
    if (q) {
      setOpen(true);
    }
  }, [q]);

  const selectOption = (asset: Asset) => {
    history.push(`/instance/assets/${asset.key.path.join('/')}`);
  };

  const matching = assets.filter((asset) => !q || matches(asset.key.path.join('/'), q));

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (matching.length) {
        const picked = matching[highlight];
        if (!picked) {
          throw new Error('Selection out of sync with suggestions');
        }
        selectOption(picked);
        e.preventDefault();
        e.stopPropagation();
      }
      return;
    }

    // Escape closes the options. The options re-open if you type another char or click.
    if (e.key === 'Escape') {
      setHighlight(0);
      setOpen(false);
      return;
    }

    const lastResult = matching.length - 1;
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlight(highlight === 0 ? lastResult : highlight - 1);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlight(highlight === lastResult ? 0 : highlight + 1);
    }
  };

  return (
    <div style={{width: 600}}>
      <Popover
        minimal
        fill={true}
        isOpen={open && matching.length > 0}
        position={'bottom-left'}
        content={
          <Menu style={{maxWidth: 600, minWidth: 600}}>
            {matching.slice(0, 10).map((asset, idx) => (
              <MenuItem
                key={idx}
                onMouseDown={(e: React.MouseEvent<any>) => {
                  e.preventDefault();
                  e.stopPropagation();
                  selectOption(asset);
                }}
                active={highlight === idx}
                icon="panel-table"
                text={
                  <div>
                    <div>{asset.key.path.join('/')}</div>
                  </div>
                }
              />
            ))}
          </Menu>
        }
      >
        <InputGroup
          type="text"
          value={q}
          width={600}
          fill={false}
          placeholder={`Search all asset_keys...`}
          onChange={(e: React.ChangeEvent<any>) => setQ(e.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
      </Popover>
    </div>
  );
};

type State = {
  checkedPaths: Set<string>;
  lastPath?: string[];
};
const initialState: State = {
  checkedPaths: new Set(),
  lastPath: undefined,
};
enum ActionType {
  TOGGLE_ONE = 'toggle-one',
  TOGGLE_SLICE = 'toggle-slice',
  TOGGLE_ALL = 'toggle-all',
}
type Action = {
  type: ActionType;
  payload: {
    checked: boolean;
    path?: string[];
    allPaths: string[][];
  };
};
const reducer = (state: State, action: Action): State => {
  const copy = new Set(Array.from(state.checkedPaths));
  switch (action.type) {
    case 'toggle-one': {
      const {checked, path} = action.payload;
      checked ? copy.add(JSON.stringify(path)) : copy.delete(JSON.stringify(path));
      return {checkedPaths: copy, lastPath: path};
    }

    case 'toggle-slice': {
      const {checked, path: actionPath, allPaths} = action.payload;
      const actionPathKey = JSON.stringify(actionPath);
      const lastPathKey = JSON.stringify(state.lastPath);
      const allPathKeys = allPaths.map((path) => JSON.stringify(path));
      const indexOfLast = allPathKeys.findIndex((key) => key === lastPathKey);
      const indexOfChecked = allPathKeys.findIndex((key) => key === actionPathKey);
      if (indexOfLast === undefined || indexOfChecked === undefined) {
        return state;
      }

      const [start, end] = [indexOfLast, indexOfChecked].sort();
      allPathKeys
        .slice(start, end + 1)
        .forEach((pathKey) => (checked ? copy.add(pathKey) : copy.delete(pathKey)));
      return {
        lastPath: actionPath,
        checkedPaths: copy,
      };
    }

    case 'toggle-all': {
      const {checked, allPaths} = action.payload;
      return {
        checkedPaths: checked ? new Set(allPaths.map((path) => JSON.stringify(path))) : new Set(),
        lastPath: undefined,
      };
    }
    default:
      return state;
  }
};

const AssetsTable = ({
  assets,
  currentPath,
  isFlattened,
  setQuery,
}: {
  assets: Asset[];
  currentPath: string[];
  setQuery: (q: string) => void;
  isFlattened: boolean;
}) => {
  useDocumentTitle(currentPath.length ? `Assets: ${currentPath.join(' \u203A ')}` : 'Assets');
  const [toWipe, setToWipe] = React.useState<AssetKey[] | undefined>();
  const {canWipeAssets} = usePermissions();
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const {checkedPaths} = state;

  const hasTags = !!assets.filter((asset) => asset.tags.length).length;
  const pathMap: {[key: string]: Asset[]} = {};
  assets.forEach((asset) => {
    const path = isFlattened
      ? asset.key.path
      : asset.key.path.slice(currentPath.length, currentPath.length + 1);
    const pathKey = JSON.stringify(path);
    pathMap[pathKey] = [...(pathMap[pathKey] || []), asset];
  });
  const sorted = Object.keys(pathMap)
    .sort()
    .map((x) => JSON.parse(x));

  const onTagClick = (tag: AssetTag) => {
    setQuery(`tag:${tag.key}=${tag.value}`);
  };
  const onChangeAll = (e: React.FormEvent<HTMLInputElement>) => {
    if (e.target instanceof HTMLInputElement) {
      const checked = checkedPaths.size !== sorted.length;
      onToggleAll(checked);
    }
  };
  const onToggleAll = (checked: boolean) => {
    dispatch({
      type: ActionType.TOGGLE_ALL,
      payload: {checked, allPaths: sorted},
    });
  };
  const onToggle = (e: React.FormEvent<HTMLInputElement>, path: string[]) => {
    if (e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      if (shiftKey && state.lastPath) {
        dispatch({
          type: ActionType.TOGGLE_SLICE,
          payload: {checked, path, allPaths: sorted},
        });
      } else {
        dispatch({
          type: ActionType.TOGGLE_ONE,
          payload: {checked, path, allPaths: sorted},
        });
      }
    }
  };

  const selectedAssets = new Set<Asset>();
  sorted.forEach((path) => {
    const key = JSON.stringify(path);
    if (checkedPaths.has(key)) {
      const assets = pathMap[key] || [];
      assets.forEach((asset) => selectedAssets.add(asset));
    }
  });

  return (
    <Box margin={{top: 20}}>
      <Table>
        <thead>
          <tr>
            {canWipeAssets ? (
              <th style={{width: 50}}>
                <div style={{display: 'flex', alignItems: 'center'}}>
                  <Checkbox
                    style={{marginBottom: 0, marginTop: 1}}
                    indeterminate={checkedPaths.size > 0 && checkedPaths.size !== sorted.length}
                    checked={checkedPaths.size === sorted.length}
                    onChange={onChangeAll}
                  />
                  <AssetActions
                    selected={Array.from(selectedAssets)}
                    clearSelection={() => onToggleAll(false)}
                  />
                </div>
              </th>
            ) : null}
            <th>Asset Key</th>
            {hasTags ? (
              <th>
                <Group direction="row" spacing={8} alignItems="center">
                  Tags
                  <Tooltip position="top" content={EXPERIMENTAL_TAGS_WARNING}>
                    <IconWIP name="info" />
                  </Tooltip>
                </Group>
              </th>
            ) : null}
            {canWipeAssets ? <th>Actions</th> : null}
          </tr>
        </thead>
        <tbody>
          {sorted.map((path, idx) => {
            const isSelected = checkedPaths.has(JSON.stringify(path));
            return (
              <AssetEntryRow
                key={idx}
                currentPath={currentPath}
                path={path}
                assets={pathMap[JSON.stringify(path)] || []}
                shouldShowTags={hasTags}
                isFlattened={isFlattened}
                isSelected={isSelected}
                onSelectToggle={onToggle}
                onTagClick={onTagClick}
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
        requery={(_) => [{query: ASSETS_TABLE_QUERY}]}
      />
    </Box>
  );
};

const AssetEntryRow: React.FC<{
  currentPath?: string[];
  path: string[];
  isSelected: boolean;
  isFlattened: boolean;
  onSelectToggle: (e: React.FormEvent<HTMLInputElement>, path: string[]) => void;
  shouldShowTags: boolean;
  assets: Asset[];
  onTagClick: (tag: AssetTag) => void;
  onWipe: (assets: Asset[]) => void;
  canWipe: boolean;
}> = React.memo(
  ({
    currentPath,
    path,
    shouldShowTags,
    assets,
    onTagClick,
    isSelected,
    isFlattened,
    onSelectToggle,
    onWipe,
    canWipe,
  }) => {
    const fullPath = [...(currentPath || []), ...path];
    const isAssetEntry = assets.length === 1 && fullPath.join('/') === assets[0].key.path.join('/');
    const linkUrl = `/instance/assets/${fullPath.map(encodeURIComponent).join('/')}`;
    return (
      <tr>
        {canWipe ? (
          <td style={{paddingRight: '4px'}}>
            <Checkbox checked={isSelected} onChange={(e) => onSelectToggle(e, path)} />
          </td>
        ) : null}
        <td>
          <Link to={linkUrl}>
            <Box flex={{alignItems: 'center'}}>
              {path
                .map((p, i) => <span key={i}>{p}</span>)
                .reduce(
                  (accum, curr, ii) => [
                    ...accum,
                    ii > 0 ? (
                      <React.Fragment key={`${ii}-space`}>&nbsp;{`>`}&nbsp;</React.Fragment>
                    ) : null,
                    curr,
                  ],
                  [] as React.ReactNode[],
                )}
              {isAssetEntry || isFlattened ? null : '/'}
            </Box>
          </Link>
        </td>
        {shouldShowTags ? (
          <td>
            {isAssetEntry && assets[0].tags.length ? (
              <Box flex={{direction: 'row', wrap: 'wrap'}}>
                {assets[0].tags.map((tag, idx) => (
                  <Tag tag={tag} key={idx} onClick={() => onTagClick(tag)} />
                ))}
              </Box>
            ) : null}
          </td>
        ) : null}
        {canWipe ? (
          <td>
            {isAssetEntry ? (
              <Popover
                content={
                  <Menu>
                    <MenuItem
                      text="Wipe ..."
                      icon="trash"
                      target="_blank"
                      onClick={() => onWipe(assets)}
                    />
                  </Menu>
                }
                position="bottom"
              >
                <Button small minimal icon="chevron-down" style={{marginLeft: '4px'}} />
              </Popover>
            ) : (
              <Button small minimal disabled icon="chevron-down" style={{marginLeft: '4px'}} />
            )}
          </td>
        ) : null}
      </tr>
    );
  },
);

const AssetActions: React.FC<{
  selected: Asset[];
  clearSelection: () => void;
}> = React.memo(({selected, clearSelection}) => {
  const [showBulkWipeDialog, setShowBulkWipeDialog] = React.useState<boolean>(false);
  const {canWipeAssets} = usePermissions();

  if (!canWipeAssets) {
    return null;
  }

  const disabled = selected.length === 0;
  const prompt = disabled
    ? 'Select assets to wipe'
    : selected.length === 1
    ? 'Wipe 1 asset'
    : `Wipe ${selected.length} assets`;

  return (
    <>
      <Tooltip position="right" content={prompt}>
        <Button
          disabled={disabled}
          icon="trash"
          intent={disabled ? undefined : 'danger'}
          onClick={() => setShowBulkWipeDialog(true)}
        >
          {disabled ? null : selected.length}
        </Button>
      </Tooltip>
      <AssetWipeDialog
        assetKeys={selected.map((asset) => asset.key)}
        isOpen={showBulkWipeDialog}
        onClose={() => setShowBulkWipeDialog(false)}
        onComplete={() => {
          setShowBulkWipeDialog(false);
          clearSelection();
        }}
        requery={(_) => [{query: ASSETS_TABLE_QUERY}]}
      />
    </>
  );
});

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  overflow: auto;
  position: relative;
  z-index: 0;
  table th {
    vertical-align: middle;
  }
`;

const ASSETS_TABLE_QUERY = gql`
  query AssetsTableQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
          id
          key {
            path
          }
          tags {
            key
            value
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const InputGroup = styled(BlueprintInputGroup)`
  input,
  input:focus {
    outline: none;
    box-shadow: none;
    border: 1px solid #ececec;
  }
`;
