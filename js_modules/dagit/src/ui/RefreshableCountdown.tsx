import {Colors, Icon, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components';

import {Group} from 'src/ui/Group';

export interface Props {
  refreshing: boolean;
  seconds: number;
  onRefresh: () => void;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh} = props;
  return (
    <Group direction="horizontal" spacing={8} alignItems="center">
      <span style={{color: Colors.GRAY3, fontVariantNumeric: 'tabular-nums'}}>
        {refreshing ? 'Refreshing data…' : `0:${seconds < 10 ? `0${seconds}` : seconds}`}
      </span>
      <Tooltip content="Refresh now">
        <RefreshButton onClick={onRefresh}>
          <Icon iconSize={11} icon="refresh" color={Colors.GRAY3} />
        </RefreshButton>
      </Tooltip>
    </Group>
  );
};

const RefreshButton = styled.button`
  border: none;
  cursor: pointer;
  padding: 0;
  margin: 0;
  outline: none;
  background-color: transparent;

  .bp3-icon {
    display: block;

    &:hover {
      svg {
        fill: ${Colors.DARK_GRAY5};
      }
    }
  }
`;
