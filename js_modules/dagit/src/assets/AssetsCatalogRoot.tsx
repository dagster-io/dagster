import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {AssetsCatalogTable} from 'src/assets/AssetsCatalogTable';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';

export const AssetsCatalogRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath = (match.params['0'] || '')
    .split('/')
    .filter((x: string) => x)
    .map(decodeURIComponent);
  const breadcrumbs: IBreadcrumbProps[] = [
    {icon: 'panel-table', text: 'Assets', href: '/instance/ssets'},
  ];

  if (currentPath.length) {
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${encodeURIComponent(elem)}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/instance/assets');
  }

  return (
    <Page>
      <PageHeader text="Assets" />
      <AssetsCatalogTable prefixPath={currentPath} />
    </Page>
  );
};
