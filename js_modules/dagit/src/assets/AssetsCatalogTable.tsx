import {gql, useQuery} from '@apollo/client';
import {
  Button,
  Menu,
  MenuItem,
  Icon,
  Popover,
  InputGroup as BlueprintInputGroup,
  NonIdealState,
  Tooltip,
  Colors,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {featureEnabled, FeatureFlag} from '../app/Util';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
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
export const AssetsCatalogTable: React.FunctionComponent<{prefixPath?: string[]}> = ({
  prefixPath,
}) => {
  const queryResult = useQuery<AssetsTableQuery>(ASSETS_TABLE_QUERY);
  const [q, setQ] = React.useState<string>('');

  return (
    <div style={{flexGrow: 1}}>
      <Loading queryResult={queryResult}>
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
          const isFlattened = !featureEnabled(FeatureFlag.DirectoryAssetCatalog);
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

          return (
            <Wrapper>
              {isFlattened ? (
                <AssetsFilter assets={assets} query={q} onSetQuery={setQ} />
              ) : (
                <AssetSearch assets={allAssets} />
              )}
              <AssetsTable assets={matching} currentPath={prefixPath || []} setQuery={setQ} />
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
    <div style={{marginBottom: 20, maxWidth: 600}}>
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
          width={300}
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

const AssetsTable = ({
  assets,
  currentPath,
  setQuery,
}: {
  assets: Asset[];
  currentPath: string[];
  setQuery: (q: string) => void;
}) => {
  useDocumentTitle(currentPath.length ? `Assets: ${currentPath.join(' \u203A ')}` : 'Assets');
  const [toWipe, setToWipe] = React.useState<AssetKey | undefined>();
  const sorted = React.useMemo(
    () =>
      [...assets].sort((a, b) =>
        a.key.path
          .join('/')
          .toLocaleLowerCase()
          .localeCompare(b.key.path.join('/').toLocaleLowerCase()),
      ),
    [assets],
  );
  const removeAsset = () => {
    setToWipe(undefined);
  };
  const isFlattened = !featureEnabled(FeatureFlag.DirectoryAssetCatalog);
  const hasTags = !!assets.filter((asset) => asset.tags.length).length;

  if (!isFlattened) {
    const pathMap: {[key: string]: Asset} = {};
    assets.forEach((asset) => {
      const [pathKey] = isFlattened
        ? [asset.key.path.join('/')]
        : asset.key.path.slice(currentPath.length, currentPath.length + 1);
      pathMap[pathKey] = asset;
    });

    const pathKeys = Object.keys(pathMap).sort();
    return (
      <Table>
        <thead>
          <tr>
            <th>Asset Key</th>
          </tr>
        </thead>
        <tbody>
          {pathKeys.map((pathKey: string) => {
            const linkUrl = `/instance/assets/${
              currentPath.length
                ? currentPath.map(encodeURIComponent).join('/') + `/${encodeURIComponent(pathKey)}`
                : encodeURIComponent(pathKey)
            }`;
            const assetKeyString = pathMap[pathKey].key.path.join('/');
            const pathString = [...currentPath, pathKey].join('/');
            return (
              <tr key={pathString}>
                <td>
                  <Link to={linkUrl}>
                    {assetKeyString === pathString ? pathKey : `${pathKey}/`}
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    );
  }

  const onClick = (tag: AssetTag) => {
    setQuery(`tag:${tag.key}=${tag.value}`);
  };

  return (
    <Box margin={{top: 20}}>
      <Table>
        <thead>
          <tr>
            <th>Asset Key</th>
            {hasTags ? (
              <th>
                <Group direction="row" spacing={8} alignItems="center">
                  Tags
                  <Tooltip position="top" content={EXPERIMENTAL_TAGS_WARNING}>
                    <Icon
                      icon={IconNames.INFO_SIGN}
                      iconSize={12}
                      style={{position: 'relative', top: '-2px'}}
                    />
                  </Tooltip>
                </Group>
              </th>
            ) : null}
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((asset: Asset, idx: number) => {
            const linkUrl = `/instance/assets/${asset.key.path.map(encodeURIComponent).join('/')}`;
            return (
              <tr key={idx}>
                <td>
                  <Link to={linkUrl}>
                    <Box flex={{alignItems: 'center'}}>
                      {asset.key.path
                        .map<React.ReactNode>((p, i) => <span key={i}>{p}</span>)
                        .reduce((prev, curr, i) => [
                          prev,
                          <Box key={`separator_${i}`} padding={{horizontal: 2}}>
                            <Icon icon={IconNames.CHEVRON_RIGHT} iconSize={12} />
                          </Box>,
                          curr,
                        ])}
                    </Box>
                  </Link>
                </td>
                {hasTags ? (
                  <td>
                    {asset.tags.length ? (
                      <Box flex={{direction: 'row', wrap: 'wrap'}}>
                        {asset.tags.map((tag, idx) => (
                          <Tag tag={tag} key={idx} onClick={() => onClick(tag)} />
                        ))}
                      </Box>
                    ) : null}
                  </td>
                ) : null}
                <td>
                  <Popover
                    content={
                      <Menu>
                        <MenuItem
                          text="Wipe asset..."
                          icon="trash"
                          target="_blank"
                          onClick={() => setToWipe(asset.key)}
                        />
                      </Menu>
                    }
                    position="bottom"
                  >
                    <Button small minimal icon="chevron-down" style={{marginLeft: '4px'}} />
                  </Popover>
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>
      <AssetWipeDialog
        assetKey={toWipe}
        onClose={() => setToWipe(undefined)}
        onComplete={removeAsset}
        requery={(_) => [{query: ASSETS_TABLE_QUERY}]}
      />
    </Box>
  );
};

const Wrapper = styled.div`
  flex: 1 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  overflow: auto;
`;

const ASSETS_TABLE_QUERY = gql`
  query AssetsTableQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
        nodes {
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
  margin-bottom: 20px;
`;
