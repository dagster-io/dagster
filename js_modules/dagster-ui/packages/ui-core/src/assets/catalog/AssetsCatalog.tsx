import {Box} from '@dagster-io/ui-components';
import React, {useEffect} from 'react';
import {useRouteMatch} from 'react-router-dom';
import {useSetRecoilState} from 'recoil';
import {ViewBreadcrumb} from 'shared/assets/ViewBreadcrumb.oss';

import {AssetCatalogTableV2} from './AssetCatalogTableV2';
import {useFullscreen} from '../../app/AppTopNav/AppTopNavContext';
import {currentPageAtom} from '../../app/analytics';

export const AssetsCatalog = React.memo(() => {
  const setCurrentPage = useSetRecoilState(currentPageAtom);
  const {path} = useRouteMatch();
  useEffect(() => {
    setCurrentPage(({specificPath}) => ({specificPath, path: `${path}?view=AssetCatalogTableV2`}));
  }, [path, setCurrentPage]);

  const {isFullScreen, setIsFullScreen} = useFullscreen();

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
        padding={{top: 12, horizontal: 24}}
        flex={{direction: 'row', alignItems: 'center', justifyContent: 'space-between'}}
        border="top"
      >
        <ViewBreadcrumb full />
      </Box>
      <AssetCatalogTableV2
        isFullScreen={isFullScreen}
        toggleFullScreen={() => setIsFullScreen((isFullScreen) => !isFullScreen)}
      />
    </div>
  );
});
