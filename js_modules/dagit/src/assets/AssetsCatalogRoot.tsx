import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {AssetsCatalogTable} from 'src/assets/AssetsCatalogTable';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Heading} from 'src/ui/Text';

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
