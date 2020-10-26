import {gql, useQuery} from '@apollo/client';
import {IBreadcrumbProps, NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components';

import {Loading} from 'src/Loading';
import {AssetView} from 'src/assets/AssetView';
import {AssetsCatalogTable} from 'src/assets/AssetsCatalogTable';
import {TopNav} from 'src/nav/TopNav';

export const AssetEntryRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath = (match.params['0'] || '').split('/').filter((x: string) => x);
  const queryResult = useQuery(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  const breadcrumbs: IBreadcrumbProps[] = [
    {icon: 'panel-table', text: 'Assets', href: '/instance/assets'},
  ];

  if (currentPath.length) {
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${elem}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/instance/assets');
  }

  return (
    <div style={{display: 'flex', flexDirection: 'column', width: '100%', overflow: 'auto'}}>
      <TopNav breadcrumbs={breadcrumbs} />
      <div style={{flexGrow: 1}}>
        <Loading queryResult={queryResult}>
          {({assetOrError}) => {
            if (assetOrError.__typename === 'AssetsNotSupportedError') {
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

            if (assetOrError.__typename === 'AssetNotFoundError') {
              return <AssetsCatalogTable prefixPath={currentPath} />;
            }

            return (
              <Wrapper>
                <AssetView assetKey={assetOrError.key} />
              </Wrapper>
            );
          }}
        </Loading>
      </div>
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

export const ASSET_ENTRY_ROOT_QUERY = gql`
  query AssetEntryRootQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      __typename
      ... on AssetsNotSupportedError {
        message
      }
      ... on Asset {
        key {
          path
        }
      }
    }
  }
`;
