import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {Redirect, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Box} from '../ui/Box';
import {IconWIP} from '../ui/Icon';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {TagWIP} from '../ui/TagWIP';
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

  return (
    <Page>
      <PageHeader
        title={
          view !== 'directory' ? (
            <Heading>{currentPath[currentPath.length - 1]}</Heading>
          ) : (
            <Box flex={{alignItems: 'center', gap: 4}}>
              {currentPath
                .map<React.ReactNode>((p, i) => <Heading key={i}>{p}</Heading>)
                .reduce((prev, curr, i) => [
                  prev,
                  <IconWIP key={`separator_${i}`} name="chevron_right" size={16} />,
                  curr,
                ])}
            </Box>
          )
        }
        tags={<TagWIP icon="asset">Asset</TagWIP>}
      />
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Loading queryResult={queryResult}>
          {({assetOrError, assetNodeOrError}) => {
            if (
              assetOrError.__typename === 'AssetNotFoundError' &&
              assetNodeOrError.__typename === 'AssetNotFoundError'
            ) {
              return <AssetsCatalogTable prefixPath={currentPath} />;
            }

            return (
              <Wrapper>
                <AssetView assetKey={{path: currentPath}} asOf={asOf} />
              </Wrapper>
            );
          }}
        </Loading>
      </Box>
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

const ASSET_ENTRY_ROOT_QUERY = gql`
  query AssetEntryRootQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      __typename
      ... on AssetNode {
        id
      }
    }
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
