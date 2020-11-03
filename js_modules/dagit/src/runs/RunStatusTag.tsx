import {Popover, Spinner, Tag} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {assertUnreachable} from 'src/Util';
import {RunStats} from 'src/runs/RunStats';
import {IRunStatus} from 'src/runs/RunStatusDots';

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
          <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
            <div style={{marginRight: '4px'}}>
              <Spinner size={10} />
            </div>
            Running
          </div>
        </StatusTag>
      );
    case 'MANAGED':
      return (
        <StatusTag minimal intent="none">
          Managed
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
