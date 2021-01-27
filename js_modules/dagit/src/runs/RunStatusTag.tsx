import {Popover, Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {assertUnreachable} from 'src/app/Util';
import {RunStats} from 'src/runs/RunStats';
import {IRunStatus} from 'src/runs/RunStatusDots';
import {Group} from 'src/ui/Group';
import {Spinner} from 'src/ui/Spinner';

export const RunStatusTag = (props: {status: IRunStatus}) => {
  const {status} = props;
  switch (status) {
    case 'QUEUED':
      return (
        <StatusTag minimal intent="none">
          Queued
        </StatusTag>
      );
    case 'SUCCESS':
      return (
        <StatusTag minimal intent="success">
          Succeeded
        </StatusTag>
      );
    case 'STARTING':
      return (
        <StatusTag minimal intent="none">
          Starting
        </StatusTag>
      );
    case 'NOT_STARTED':
      return (
        <StatusTag minimal intent="none">
          Not started
        </StatusTag>
      );
    case 'FAILURE':
      return (
        <StatusTag minimal intent="danger">
          Failed
        </StatusTag>
      );
    case 'STARTED':
      return (
        <StatusTag minimal intent="primary">
          <Group direction="row" spacing={4} alignItems="center">
            <Spinner purpose="body-text" />
            <div>Started</div>
          </Group>
        </StatusTag>
      );
    case 'MANAGED':
      return (
        <StatusTag minimal intent="none">
          Managed
        </StatusTag>
      );
    case 'CANCELING':
      return (
        <StatusTag minimal intent="none">
          Canceling
        </StatusTag>
      );
    case 'CANCELED':
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
  status: IRunStatus;
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

const StatusTag = styled(Tag)`
  cursor: default;
  user-select: none;
`;
