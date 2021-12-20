import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';

import {AssetPageHeader} from './AssetPageHeader';
import {AssetView} from './AssetView';
import {AssetsCatalogTable} from './AssetsCatalogTable';
import {AssetEntryRootQuery} from './types/AssetEntryRootQuery';

export const AssetEntryRoot = () => {
  const params = useParams();
  const currentPath: string[] = (params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  const queryResult = useQuery<AssetEntryRootQuery>(ASSET_ENTRY_ROOT_QUERY, {
    variables: {assetKey: {path: currentPath}},
  });

  return queryResult.loading ? (
    <Page>
      <AssetPageHeader currentPath={currentPath} />
      <Loading queryResult={queryResult}>{() => null}</Loading>
    </Page>
  ) : queryResult.data?.assetOrError.__typename === 'AssetNotFoundError' ? (
    <Page>
      <AssetPageHeader currentPath={currentPath} />
      <AssetsCatalogTable prefixPath={currentPath} />
    </Page>
  ) : (
    <Page>
      <AssetView assetKey={{path: currentPath}} />
    </Page>
  );
};

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
