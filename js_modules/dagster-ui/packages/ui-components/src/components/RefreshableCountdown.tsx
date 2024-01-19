import styled from 'styled-components';

import {Colors} from './Color';
import {Group} from './Group';
import {Icon, IconWrapper} from './Icon';
import {Tooltip} from './Tooltip';
import {secondsToCountdownTime} from './secondsToCountdownTime';

interface Props {
  refreshing: boolean;
  seconds?: number;
  onRefresh: () => void;
  dataDescription?: string;
}

export const RefreshableCountdown = (props: Props) => {
  const {refreshing, seconds, onRefresh, dataDescription = 'data'} = props;
  return (
    <Group direction="row" spacing={8} alignItems="center">
      <span
        style={{
          color: Colors.textLight(),
          fontVariantNumeric: 'tabular-nums',
          whiteSpace: 'nowrap',
        }}
      >
        {refreshing
          ? `Refreshing ${dataDescription}…`
          : seconds === undefined
          ? null
          : secondsToCountdownTime(seconds)}
      </span>
      <Tooltip content={<span style={{whiteSpace: 'nowrap'}}>Refresh now</span>} position="top">
        <RefreshButton onClick={onRefresh}>
          <Icon name="refresh" color={Colors.accentGray()} />
        </RefreshButton>
      </Tooltip>
    </Group>
  );
};

export const RefreshButton = styled.button`
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
      color: ${Colors.accentGrayHover()};
    }
  }
`;
