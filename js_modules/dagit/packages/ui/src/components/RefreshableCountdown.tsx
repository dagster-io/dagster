import * as React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {Group} from './Group';
import {IconWIP, IconWrapper} from './Icon';
import {Tooltip} from './Tooltip';

interface Props {
  refreshing: boolean;
  seconds: number;
  onRefresh: () => void;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh} = props;
  return (
    <Group direction="row" spacing={8} alignItems="center">
      <span
        style={{color: ColorsWIP.Gray400, fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap'}}
      >
        {refreshing ? 'Refreshing data…' : `0:${seconds < 10 ? `0${seconds}` : seconds}`}
      </span>
      <Tooltip content={<span style={{whiteSpace: 'nowrap'}}>Refresh now</span>} position="bottom">
        <RefreshButton onClick={onRefresh}>
          <IconWIP name="refresh" color={ColorsWIP.Gray400} />
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
      color: ${ColorsWIP.Dark};
    }
  }
`;
