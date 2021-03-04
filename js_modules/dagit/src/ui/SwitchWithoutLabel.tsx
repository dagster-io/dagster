import {Switch} from '@blueprintjs/core';
import styled from 'styled-components';

export const SwitchWithoutLabel = styled(Switch)`
  &.bp3-control.bp3-switch {
    margin-bottom: 0;
  }

  &.bp3-control.bp3-switch:not(.bp3-align-right) .bp3-control-indicator {
    margin-left: 0;
  }

  &.bp3-control .bp3-control-indicator {
    margin-right: 0;
  }

  &.bp3-control.bp3-switch:not(.bp3-align-right),
  &.bp3-control.bp3-switch.bp3-large:not(.bp3-align-right) {
    padding-left: 0;
  }
`;
