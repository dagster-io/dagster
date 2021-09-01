import {Colors, Icon} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import styled from 'styled-components/macro';

import {Group} from './Group';

interface Props {
  refreshing: boolean;
  seconds: number;
  onRefresh: () => void;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh} = props;
  return (
    <Group direction="row" spacing={8} alignItems="center">
      <span style={{color: Colors.GRAY3, fontVariantNumeric: 'tabular-nums'}}>
        {refreshing ? 'Refreshing data…' : `0:${seconds < 10 ? `0${seconds}` : seconds}`}
      </span>
      <Tooltip content="Refresh now" position="bottom">
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
