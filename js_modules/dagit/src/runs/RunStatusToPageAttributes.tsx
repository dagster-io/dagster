import * as React from 'react';
import {PipelineRunStatus} from '../types/globalTypes';
import {RunStatusPipelineRunFragment} from './types/RunStatusPipelineRunFragment';
import gql from 'graphql-tag';

const link = (document.querySelector("link[rel*='icon']") ||
  document.createElement('link')) as HTMLLinkElement;
link.type = 'image/x-icon';
link.rel = 'shortcut icon';
document.getElementsByTagName('head')[0].appendChild(link);

const title = document.querySelector('title') as HTMLTitleElement;

const FaviconsForStatus = {
  [PipelineRunStatus.FAILURE]: '/favicon_failed.ico',
  [PipelineRunStatus.STARTED]: '/favicon_pending.ico',
  [PipelineRunStatus.NOT_STARTED]: '/favicon_pending.ico',
  [PipelineRunStatus.SUCCESS]: '/favicon_success.ico',
};

export class RunStatusToPageAttributes extends React.Component<{
  run: RunStatusPipelineRunFragment;
}> {
  static fragments = {
    RunStatusPipelineRunFragment: gql`
      fragment RunStatusPipelineRunFragment on PipelineRun {
        runId
        status
        pipeline {
          name
        }
      }
    `,
  };

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
