import {Popover} from '@blueprintjs/core';
import * as React from 'react';

import {assertUnreachable} from '../app/Util';
import {PipelineRunStatus} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {Spinner} from '../ui/Spinner';
import {TagWIP} from '../ui/TagWIP';

import {RunStats} from './RunStats';

export const RunStatusTag = (props: {status: PipelineRunStatus}) => {
  const {status} = props;
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return (
        <TagWIP minimal intent="none">
          Queued
        </TagWIP>
      );
    case PipelineRunStatus.SUCCESS:
      return (
        <TagWIP minimal intent="success">
          Success
        </TagWIP>
      );
    case PipelineRunStatus.STARTING:
      return (
        <TagWIP minimal intent="none">
          Starting
        </TagWIP>
      );
    case PipelineRunStatus.NOT_STARTED:
      return (
        <TagWIP minimal intent="none">
          Not started
        </TagWIP>
      );
    case PipelineRunStatus.FAILURE:
      return (
        <TagWIP minimal intent="danger">
          Failure
        </TagWIP>
      );
    case PipelineRunStatus.STARTED:
      return (
        <TagWIP minimal intent="primary">
          <Group direction="row" spacing={4} alignItems="center">
            <Spinner purpose="body-text" />
            <div>Started</div>
          </Group>
        </TagWIP>
      );
    case PipelineRunStatus.MANAGED:
      return (
        <TagWIP minimal intent="none">
          Managed
        </TagWIP>
      );
    case PipelineRunStatus.CANCELING:
      return (
        <TagWIP minimal intent="none">
          Canceling
        </TagWIP>
      );
    case PipelineRunStatus.CANCELED:
      return (
        <TagWIP minimal intent="danger">
          Canceled
        </TagWIP>
      );
    default:
      return assertUnreachable(status);
  }
};

interface Props {
  runId: string;
  status: PipelineRunStatus;
}

export const RunStatusTagWithStats = (props: Props) => {
  const {runId, status} = props;
  return (
    <Popover
      position={'bottom'}
      interactionKind={'hover'}
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
      usePortal
    >
      <RunStatusTag status={status} />
    </Popover>
  );
};
