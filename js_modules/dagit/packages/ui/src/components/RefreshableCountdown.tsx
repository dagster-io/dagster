import * as React from 'react';
import styled from 'styled-components/macro';

import {Colors} from './Colors';
import {Group} from './Group';
import {Icon, IconWrapper} from './Icon';
import {Tooltip} from './Tooltip';

interface Props {
  refreshing: boolean;
  seconds: number;
  onRefresh: () => void;
  dataDescription?: string;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh, dataDescription = 'data'} = props;
  return (
    <Group direction="row" spacing={8} alignItems="center">
      <span
        style={{color: Colors.Gray400, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}
      >
        {refreshing
          ? `Refreshing ${dataDescription}…`
          : `0:${seconds < 10 ? `0${seconds}` : seconds}`}
      </span>
      <Tooltip content={<span style={{whiteSpace: 'nowrap'}}>Refresh now</span>} position="bottom">
        <RefreshButton onClick={onRefresh}>
          <Icon name="refresh" color={Colors.Gray400} />
        </RefreshButton>
      </Tooltip>
    </Group>
  );
};

const RefreshButton = styled.button`
  border: none;
  cursor: pointer;
  padding: 8px;
  margin: -8px;
  outline: none;
  background-color: transparent;
  position: relative;
  top: 1px;

  & ${IconWrapper} {
    display: block;
    transition: color 100ms linear;

    &:hover {
      color: ${Colors.Dark};
    }
  }
`;
