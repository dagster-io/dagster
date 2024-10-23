import {Tooltip} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const WarningTooltip = styled(Tooltip)`
  display: block;
  outline: none;

  .bp5-popover-target,
  .bp5-icon {
    display: block;
  }

  .bp5-icon:focus,
  .bp5-icon:active {
    outline: none;
  }
`;
