import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {Group} from '../ui/Group';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AssetsCatalogTable} from './AssetsCatalogTable';

export const AssetsCatalogRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);

  return (
    <Page>
      <Group direction="column" spacing={12}>
        <PageHeader title={<Heading>Assets</Heading>} />
        <AssetsCatalogTable prefixPath={currentPath} />
      </Group>
    </Page>
  );
};
