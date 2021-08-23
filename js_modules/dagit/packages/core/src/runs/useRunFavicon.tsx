import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {PipelineRunStatus} from '../types/globalTypes';

const link = (document.querySelector("link[rel*='icon']") ||
  document.createElement('link')) as HTMLLinkElement;
link.type = 'image/x-icon';
link.rel = 'shortcut icon';
document.getElementsByTagName('head')[0].appendChild(link);

const FaviconsForStatus = {
  [PipelineRunStatus.FAILURE]: '/favicon_failed.ico',
  [PipelineRunStatus.CANCELED]: '/favicon_failed.ico',
  [PipelineRunStatus.STARTED]: '/favicon_pending.ico',
  [PipelineRunStatus.NOT_STARTED]: '/favicon_pending.ico',
  [PipelineRunStatus.STARTING]: '/favicon_pending.ico',
  [PipelineRunStatus.CANCELING]: '/favicon_pending.ico',
  [PipelineRunStatus.QUEUED]: '/favicon_pending.ico',
  [PipelineRunStatus.SUCCESS]: '/favicon_success.ico',
};

export const useRunFavicon = (status: PipelineRunStatus | undefined) => {
  const {basePath} = React.useContext(AppContext);

  const filePath = status ? FaviconsForStatus[status] : '/favicon.ico';
  const faviconHref = `${basePath}${filePath}`;

  React.useEffect(() => {
    link.href = faviconHref;
    return () => {
      link.href = '/favicon.ico';
    };
  }, [faviconHref]);
};
