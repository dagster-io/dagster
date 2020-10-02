import {
  IBreadcrumbProps,
  InputGroup,
  Menu,
  MenuItem,
  NonIdealState,
  Popover,
} from '@blueprintjs/core';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {useHistory} from 'react-router';
import {Link, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components';

import {Legend, LegendColumn, RowColumn, RowContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {AssetRoot} from 'src/assets/AssetRoot';
import {AssetsRootQuery_assetsOrError_AssetConnection_nodes} from 'src/assets/types/AssetsRootQuery';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {TopNav} from 'src/nav/TopNav';

type Asset = AssetsRootQuery_assetsOrError_AssetConnection_nodes;

export const AssetsRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const urlPathString = match.params['0'];
  const queryResult = useQuery(ASSETS_ROOT_QUERY);

  const currentPath = (urlPathString || '').split('/').filter((x: string) => x);

  const breadcrumbs: IBreadcrumbProps[] = [{icon: 'panel-table', text: 'Assets', href: '/assets'}];
  if (currentPath.length) {
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${elem}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/assets');
  }

  return (
    <div style={{display: 'flex', flexDirection: 'column', width: '100%'}}>
      <TopNav breadcrumbs={breadcrumbs} />
      <div style={{flexGrow: 1}}>
        <Loading queryResult={queryResult}>
          {({assetsOrError}) => {
            if (assetsOrError.__typename === 'AssetsNotSupportedError') {
              return (
                <Wrapper>
                  <NonIdealState
                    icon="panel-table"
                    title="Assets"
                    description={
                      <p>
                        An asset-aware event storage (e.g. <code>PostgresEventLogStorage</code>)
                        must be configured in order to use any Asset-based features. You can
                        configure this on your instance through <code>dagster.yaml</code>. See the{' '}
                        <a href="https://docs.dagster.io/overview/instances/dagster-instance">
                          instance documentation
                        </a>{' '}
                        for more information.
                      </p>
                    }
                  />
                </Wrapper>
              );
            }

            const [exactMatchingAsset] = assetsOrError.nodes.filter(
              (asset: Asset) => asset.key.path.join('/') === urlPathString,
            );
            const prefixMatchingAssets = assetsOrError.nodes.filter(
              (asset: Asset) =>
                currentPath.length < asset.key.path.length &&
                currentPath.every((part: string, i: number) => part === asset.key.path[i]),
            );

            if (!prefixMatchingAssets.length && !exactMatchingAsset) {
              return (
                <Wrapper>
                  <NonIdealState
                    icon="panel-table"
                    title="Assets"
                    description={
                      <p>
                        There are no {urlPathString ? 'matching ' : 'known '}
                        materialized assets with {urlPathString ? 'the ' : 'a '}
                        specified asset key. Any asset keys that have been specified with a{' '}
                        <code>Materialization</code> during a pipeline run will appear here. See the{' '}
                        <a href="https://docs.dagster.io/_apidocs/solids#dagster.AssetMaterialization">
                          Materialization documentation
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
                {prefixMatchingAssets.length ? (
                  <AssetsTable assets={prefixMatchingAssets} currentPath={currentPath} />
                ) : null}
                {exactMatchingAsset ? <AssetRoot assetKey={exactMatchingAsset.key} /> : null}
              </Wrapper>
            );
          }}
        </Loading>
      </div>
    </div>
  );
};

interface ActiveSuggestionInfo {
  text: string;
  idx: number;
}

const AssetSearch = ({assets}: {assets: Asset[]}) => {
  const history = useHistory();
  const [open, setOpen] = React.useState(false);
  const [q, setQ] = React.useState<string>('');
  const [active, setActive] = React.useState<ActiveSuggestionInfo | null>(null);

  const selectOption = (asset: Asset) => {
    console.log('wtf', asset);
    history.push(`/assets/${asset.key.path.join('/')}`);
  };

  const matching = assets.filter((asset) => !q || matches(asset.key.path.join('.'), q));

  const onKeyDown = (e: React.KeyboardEvent<any>) => {
    // Enter and Return confirm the currently selected suggestion or
    // confirm the freeform text you've typed if no suggestions are shown.
    if (e.key === 'Enter' || e.key === 'Return' || e.key === 'Tab') {
      if (active) {
        const picked = assets.find((asset) => asset.key.path.join('.') === active.text);
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
      setActive(null);
      setOpen(false);
      return;
    }

    if (!open && e.key !== 'Delete' && e.key !== 'Backspace') {
      setOpen(true);
    }

    // The up/down arrow keys shift selection in the dropdown.
    // Note: The first down arrow press activates the first item.
    const shift = {ArrowDown: 1, ArrowUp: -1}[e.key];
    if (shift && assets.length > 0) {
      e.preventDefault();
      let idx = (active ? active.idx : -1) + shift;
      idx = Math.max(0, Math.min(idx, assets.length - 1));
      setActive({text: assets[idx].key.path.join('.'), idx});
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
                  setActive(null);
                }}
                active={active ? active.idx === idx : false}
                icon="panel-table"
                text={
                  <div>
                    <div>{asset.key.path.join('.')}</div>
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

const matches = (haystack: string, needle: string) =>
  needle
    .toLowerCase()
    .split(' ')
    .filter((x) => x)
    .every((word) => haystack.toLowerCase().includes(word));

const AssetsTable = ({assets, currentPath}: {assets: Asset[]; currentPath: string[]}) => {
  useDocumentTitle(currentPath.length ? `Assets: ${currentPath.join('.')}` : 'Assets');
  const pathMap: {[key: string]: Asset} = {};
  assets.forEach((asset) => {
    const [pathKey] = asset.key.path.slice(currentPath.length, currentPath.length + 1);
    pathMap[pathKey] = asset;
  });

  const pathKeys = Object.keys(pathMap).sort();

  return (
    <div style={{margin: '16px'}}>
      {currentPath.length ? null : (
        <div style={{marginBottom: 30}}>
          <AssetSearch assets={assets} />
        </div>
      )}
      <Legend>
        <LegendColumn>Asset Key</LegendColumn>
      </Legend>
      {pathKeys.map((pathKey: string, idx: number) => {
        const linkUrl = `/assets/${
          currentPath.length ? currentPath.join('/') + `/${pathKey}` : pathKey
        }`;
        return (
          <RowContainer key={idx}>
            <RowColumn>
              <Link to={linkUrl}>{pathKey}</Link>
            </RowColumn>
          </RowContainer>
        );
      })}
    </div>
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

export const ASSETS_ROOT_QUERY = gql`
  query AssetsRootQuery {
    assetsOrError {
      __typename
      ... on AssetsNotSupportedError {
        message
      }
      ... on AssetConnection {
        nodes {
          key {
            path
          }
        }
      }
    }
  }
`;
