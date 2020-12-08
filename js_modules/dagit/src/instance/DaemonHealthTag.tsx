import {Tag, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {DaemonHealthFragment_allDaemonStatuses as DaemonStatus} from 'src/instance/types/DaemonHealthFragment';

interface DaemonHealthTagProps {
  daemon: DaemonStatus;
  tooltip?: string;
}

export const DaemonHealthTag = (props: DaemonHealthTagProps) => {
  const {daemon, tooltip} = props;

  const tag = () => {
    if (daemon.healthy) {
      return (
        <HoverTag minimal intent="success">
          Running
        </HoverTag>
      );
    }

    if (daemon.required) {
      return (
        <HoverTag minimal intent="danger">
          Not running
        </HoverTag>
      );
    }

    return (
      <HoverTag minimal intent="none">
        Not enabled
      </HoverTag>
    );
  };

  if (tooltip) {
    return (
      <Tooltip content={tooltip} position="top">
        {tag()}
      </Tooltip>
    );
  }

  return tag();
};

const HoverTag = styled(Tag)`
  cursor: pointer;
  user-select: none;
`;
