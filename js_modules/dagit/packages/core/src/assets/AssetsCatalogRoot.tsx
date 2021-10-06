import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {Box} from '../ui/Box';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AssetsCatalogTable} from './AssetsCatalogTable';

export const AssetsCatalogRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  return (
    <div>
      <PageHeader title={<Heading>Assets</Heading>} />
      <Box padding={{vertical: 16}}>
        <AssetsCatalogTable prefixPath={currentPath} />
      </Box>
    </div>
  );
};
