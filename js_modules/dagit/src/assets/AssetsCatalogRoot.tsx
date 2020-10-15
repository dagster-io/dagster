import {IBreadcrumbProps} from '@blueprintjs/core';
import * as React from 'react';
import {RouteComponentProps} from 'react-router-dom';

import {AssetsCatalogTable} from 'src/assets/AssetsCatalogTable';
import {TopNav} from 'src/nav/TopNav';

export const AssetsCatalogRoot: React.FunctionComponent<RouteComponentProps> = ({match}) => {
  const currentPath = (match.params['0'] || '').split('/').filter((x: string) => x);
  const breadcrumbs: IBreadcrumbProps[] = [{icon: 'panel-table', text: 'Assets', href: '/assets'}];
  if (currentPath.length) {
    currentPath.reduce((accum: string, elem: string) => {
      const href = `${accum}/${elem}`;
      breadcrumbs.push({text: elem, href});
      return href;
    }, '/assets');
  }

  return (
    <div style={{display: 'flex', flexDirection: 'column', width: '100%', overflow: 'auto'}}>
      <TopNav breadcrumbs={breadcrumbs} />
      <AssetsCatalogTable prefixPath={currentPath} />
    </div>
  );
};
