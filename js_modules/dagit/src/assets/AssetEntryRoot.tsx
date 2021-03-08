import {gql, useQuery} from '@apollo/client';
import {Colors, Breadcrumbs, IBreadcrumbProps, Icon} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components';

import {featureEnabled, FeatureFlag} from 'src/app/Util';
import {AssetView} from 'src/assets/AssetView';
import {AssetsCatalogTable} from 'src/assets/AssetsCatalogTable';
import {AssetEntryRootQuery} from 'src/assets/types/AssetEntryRootQuery';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';

export const AssetEntryRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath: string[] = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const queryResult = useQuery<AssetEntryRootQuery>(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  const pathDetails = () => {
    if (currentPath.length === 1 || featureEnabled(FeatureFlag.AssetCatalog)) {
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
            featureEnabled(FeatureFlag.AssetCatalog) ? (
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
            ) : (
              <Heading>{currentPath[currentPath.length - 1]}</Heading>
            )
          }
          icon="th"
          description={<PathDetails>{pathDetails()}</PathDetails>}
        />
        <Loading queryResult={queryResult}>
          {({assetOrError}) => {
            if (assetOrError.__typename === 'AssetNotFoundError') {
              if (featureEnabled(FeatureFlag.AssetCatalog)) {
                return <AssetsCatalogTable />;
              }
              return <AssetsCatalogTable prefixPath={currentPath} />;
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
