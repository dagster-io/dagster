import {gql, useQuery} from '@apollo/client';
import {BreadcrumbProps, Breadcrumbs} from '@blueprintjs/core';
import * as React from 'react';
import {Link, Redirect, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {AssetEntryRootQuery} from './types/AssetEntryRootQuery';
import {useAssetView} from './useAssetView';

// Jan 1, 2015 at 00:00 GMT
const EARLIEST_TIME = 1420070400000;

export const AssetEntryRoot: React.FC<RouteComponentProps> = ({location, match}) => {
  const currentPath: string[] = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const {pathname, search} = location;
  const asOf = React.useMemo(() => {
    const params = new URLSearchParams(search);
    return params.get('asOf');
  }, [search]);

  // Validate the `asOf` time, since it's user-specified.
  const invalidTime = React.useMemo(() => {
    const asOfNumber = Number(asOf);
    return asOfNumber && (asOfNumber < EARLIEST_TIME || asOfNumber > Date.now());
  }, [asOf]);

  const [view] = useAssetView();

  const queryResult = useQuery<AssetEntryRootQuery>(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  // If the asOf timestamp is invalid, discard it via redirect.
  if (invalidTime) {
    return <Redirect to={pathname} />;
  }

  const pathDetails = () => {
    if (currentPath.length === 1 || view !== 'directory') {
      return <Link to="/instance/assets">Assets</Link>;
    }

    const breadcrumbs: BreadcrumbProps[] = [];
    currentPath.slice(0, currentPath.length - 1).reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/instance/assets');

    return (
      <Box flex={{direction: 'row', alignItems: 'center'}} style={{maxWidth: 500}}>
        <Box margin={{right: 4}}>
          <Link to="/instance/assets">Assets</Link>:
        </Box>
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
      <Group direction="column" spacing={20} padding={{horizontal: 24}}>
        <PageHeader
          title={
            view !== 'directory' ? (
              <Heading>{currentPath[currentPath.length - 1]}</Heading>
            ) : (
              <Box flex={{alignItems: 'center'}}>
                {currentPath
                  .map<React.ReactNode>((p, i) => <Heading key={i}>{p}</Heading>)
                  .reduce((prev, curr, i) => [
                    prev,
                    <Box key={`separator_${i}`} padding={4}>
                      <IconWIP name="chevron_right" size={24} />
                    </Box>,
                    curr,
                  ])}
              </Box>
            )
          }
          icon="table_view"
          description={<PathDetails>{pathDetails()}</PathDetails>}
        />
        <Loading queryResult={queryResult}>
          {({assetOrError}) => {
            if (assetOrError.__typename === 'AssetNotFoundError') {
              return <AssetsCatalogTable prefixPath={currentPath} />;
            }

            return (
              <Wrapper>
                <AssetView assetKey={assetOrError.key} asOf={asOf} />
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
  color: ${ColorsWIP.Gray500};

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
        id
        key {
          path
        }
      }
    }
  }
`;
