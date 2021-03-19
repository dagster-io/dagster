import {gql, useQuery} from '@apollo/client';
import {Colors, Breadcrumbs, IBreadcrumbProps, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {featureEnabled, FeatureFlag} from '../app/Util';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {AssetEntryRootQuery} from './types/AssetEntryRootQuery';

export const AssetEntryRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath: string[] = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const queryResult = useQuery<AssetEntryRootQuery>(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  const pathDetails = () => {
    if (currentPath.length === 1 || !featureEnabled(FeatureFlag.DirectoryAssetCatalog)) {
      return <Link to="/instance/assets">Asset</Link>;
    }

    const breadcrumbs: IBreadcrumbProps[] = [];
    currentPath.slice(0, currentPath.length - 1).reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/instance/assets');

    return (
      <Box flex={{direction: 'row', alignItems: 'center'}} style={{maxWidth: 500}}>
        <div style={{marginRight: '5px'}}>
          <Link to="/instance/assets">Asset</Link> in
        </div>
        <Breadcrumbs
          breadcrumbRenderer={({text, href}) => (
            <Link to={href || '#'}>
              <span style={{fontSize: '14px'}}>{text}</span>
            </Link>
          )}
          items={breadcrumbs}
        />
      </Box>
    );
  };

  return (
    <Page>
      <Group direction="column" spacing={20}>
        <PageHeader
          title={
            featureEnabled(FeatureFlag.DirectoryAssetCatalog) ? (
              <Heading>{currentPath[currentPath.length - 1]}</Heading>
            ) : (
              <Box flex={{alignItems: 'center'}}>
                {currentPath
                  .map<React.ReactNode>((p, i) => <Heading key={i}>{p}</Heading>)
                  .reduce((prev, curr, i) => [
                    prev,
                    <Box key={`separator_${i}`} padding={4}>
                      <Icon icon={IconNames.CHEVRON_RIGHT} iconSize={18} />
                    </Box>,
                    curr,
                  ])}
              </Box>
            )
          }
          icon="th"
          description={<PathDetails>{pathDetails()}</PathDetails>}
        />
        <Loading queryResult={queryResult}>
          {({assetOrError}) => {
            if (assetOrError.__typename === 'AssetNotFoundError') {
              if (featureEnabled(FeatureFlag.DirectoryAssetCatalog)) {
                return <AssetsCatalogTable prefixPath={currentPath} />;
              }
              return <AssetsCatalogTable />;
            }

            return (
              <Wrapper>
                <AssetView assetKey={assetOrError.key} />
              </Wrapper>
            );
          }}
        </Loading>
      </Group>
    </Page>
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

const PathDetails = styled.div`
  color: ${Colors.GRAY2};

  .bp3-breadcrumbs {
    height: auto;
  }

  .bp3-breadcrumbs-collapsed {
    position: relative;
    top: 2px;
    margin-left: 2px;
  }
`;

const ASSET_ENTRY_ROOT_QUERY = gql`
  query AssetEntryRootQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      __typename
      ... on Asset {
        key {
          path
        }
      }
    }
  }
`;
