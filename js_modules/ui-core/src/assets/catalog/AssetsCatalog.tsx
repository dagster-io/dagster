import {Box} from '@dagster-io/ui-components';
import {ViewBreadcrumb} from '@shared/assets/ViewBreadcrumb';
import React from 'react';

import {AssetCatalogTableV2} from './AssetCatalogTableV2';

export const AssetsCatalog = React.memo(() => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateRows: 'auto minmax(0, 1fr)',
        height: '100%',
        overflow: 'scroll',
      }}
    >
      <Box
        padding={{top: 8, horizontal: 24}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        style={{width: '100%', minHeight: 44, marginBottom: -4}}
      >
        <ViewBreadcrumb />
      </Box>
      <AssetCatalogTableV2 />
    </div>
  );
});
