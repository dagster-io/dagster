import styled from 'styled-components/macro';

import {Tooltip} from '../ui/Tooltip';

export const WarningTooltip = styled(Tooltip)`
  display: block;
  outline: none;

  .bp3-popover-target,
  .bp3-icon {
    display: block;
  }

  .bp3-icon:focus,
  .bp3-icon:active {
    outline: none;
  }
`;
