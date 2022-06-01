import {PageHeader, Heading} from '@dagster-io/ui';
import * as React from 'react';
import {useParams} from 'react-router-dom';

import {ReloadAllButton} from '../workspace/ReloadAllButton';

import {AssetsCatalogTable} from './AssetsCatalogTable';

export const AssetsCatalogRoot = () => {
  const params = useParams();
  const prefixPath = (params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  return (
    <div>
      <PageHeader
        title={<Heading>Assets</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <AssetsCatalogTable prefixPath={prefixPath} />
    </div>
  );
};
