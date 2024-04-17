import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

export const AutomaterializeDot = styled.div<{$paused: boolean | undefined}>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: ${({$paused}) =>
    $paused === false ? Colors.accentBlue() : Colors.accentGray()};
`;
