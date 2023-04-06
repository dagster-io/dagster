import {Tooltip} from '@dagster-io/ui';
import styled from 'styled-components/macro';

export const WarningTooltip = styled(Tooltip)`
  display: block;
  outline: none;

  .bp4-popover-target,
  .bp4-icon {
    display: block;
  }

  .bp4-icon:focus,
  .bp4-icon:active {
    outline: none;
  }
`;
