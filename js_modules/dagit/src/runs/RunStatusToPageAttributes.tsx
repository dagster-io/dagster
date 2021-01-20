import {gql} from '@apollo/client';
import * as React from 'react';

import {RunStatusPipelineRunFragment} from 'src/runs/types/RunStatusPipelineRunFragment';
import {PipelineRunStatus} from 'src/types/globalTypes';

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

export class RunStatusToPageAttributes extends React.Component<{
  run: RunStatusPipelineRunFragment;
}> {
  componentDidMount() {
    this.updatePageAttributes();
  }

  componentDidUpdate() {
    this.updatePageAttributes();
  }

  componentWillUnmount() {
    link.href = '/favicon.ico';
    title.textContent = 'Dagit';
  }

  updatePageAttributes() {
    const {status, pipeline, runId} = this.props.run;

    title.textContent = `${pipeline.name} ${runId} [${status}]`;
    link.href = FaviconsForStatus[status] || '/favicon.ico';
  }

  render() {
    return <span />;
  }
}

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
