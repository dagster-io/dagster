import {Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {assertUnreachable} from '../app/Util';
import {PipelineRunStatus} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {Popover} from '../ui/Popover';
import {Spinner} from '../ui/Spinner';

import {RunStats} from './RunStats';

export const RunStatusTag = (props: {status: PipelineRunStatus}) => {
  const {status} = props;
  switch (status) {
    case PipelineRunStatus.QUEUED:
      return (
        <StatusTag minimal intent="none">
          Queued
        </StatusTag>
      );
    case PipelineRunStatus.SUCCESS:
      return (
        <StatusTag minimal intent="success">
          Success
        </StatusTag>
      );
    case PipelineRunStatus.STARTING:
      return (
        <StatusTag minimal intent="none">
          Starting
        </StatusTag>
      );
    case PipelineRunStatus.NOT_STARTED:
      return (
        <StatusTag minimal intent="none">
          Not started
        </StatusTag>
      );
    case PipelineRunStatus.FAILURE:
      return (
        <StatusTag minimal intent="danger">
          Failure
        </StatusTag>
      );
    case PipelineRunStatus.STARTED:
      return (
        <StatusTag minimal intent="primary">
          <Group direction="row" spacing={4} alignItems="center">
            <Spinner purpose="body-text" />
            <div>Started</div>
          </Group>
        </StatusTag>
      );
    case PipelineRunStatus.MANAGED:
      return (
        <StatusTag minimal intent="none">
          Managed
        </StatusTag>
      );
    case PipelineRunStatus.CANCELING:
      return (
        <StatusTag minimal intent="none">
          Canceling
        </StatusTag>
      );
    case PipelineRunStatus.CANCELED:
      return (
        <StatusTag minimal intent="danger">
          Canceled
        </StatusTag>
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
      position="bottom-left"
      interactionKind="hover"
      content={<RunStats runId={runId} />}
      hoverOpenDelay={100}
      usePortal
    >
      <RunStatusTag status={status} />
    </Popover>
  );
};

const StatusTag = styled(Tag)`
  cursor: default;
  text-transform: uppercase;
  user-select: none;
`;
