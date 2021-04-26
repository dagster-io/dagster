import {gql} from '@apollo/client';
import * as React from 'react';

import {AppContext} from '../app/AppContext';
import {PipelineRunStatus} from '../types/globalTypes';

import {RunStatusPipelineRunFragment} from './types/RunStatusPipelineRunFragment';

const link = (document.querySelector("link[rel*='icon']") ||
  document.createElement('link')) as HTMLLinkElement;
link.type = 'image/x-icon';
link.rel = 'shortcut icon';
document.getElementsByTagName('head')[0].appendChild(link);

const title = document.querySelector('title') as HTMLTitleElement;

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

export const RunStatusToPageAttributes: React.FC<{run: RunStatusPipelineRunFragment}> = ({run}) => {
  const {basePath} = React.useContext(AppContext);

  React.useEffect(() => {
    const {status, pipeline, runId} = run;
    title.textContent = `${pipeline.name} ${runId} [${status}]`;
    link.href = `${basePath}${FaviconsForStatus[status] || '/favicon.ico'}`;

    () => {
      link.href = '/favicon.ico';
      title.textContent = 'Dagit';
    };
  }, [basePath, run]);

  return <span />;
};

export const RUN_STATUS_PIPELINE_RUN_FRAGMENT = gql`
  fragment RunStatusPipelineRunFragment on PipelineRun {
    id
    runId
    status
    pipeline {
      name
    }
  }
`;
