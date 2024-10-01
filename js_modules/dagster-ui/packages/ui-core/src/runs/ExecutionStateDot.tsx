import {Colors} from '@dagster-io/ui-components';
import styled from 'styled-components';

import {IStepState} from './RunMetadataProvider';

export const ExecutionStateDot = styled.div<{state: IStepState}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  transition: background 200ms linear;
  background: ${({state}) =>
    ({
      [IStepState.RUNNING]: Colors.accentGray(),
      [IStepState.SUCCEEDED]: Colors.accentGreen(),
      [IStepState.SKIPPED]: Colors.accentYellow(),
      [IStepState.FAILED]: Colors.accentRed(),
      [IStepState.PREPARING]: Colors.accentRed(),
      [IStepState.RETRY_REQUESTED]: Colors.accentRed(),
      [IStepState.UNKNOWN]: Colors.accentRed(),
    })[state]};
  &:hover {
    background: ${({state}) =>
      ({
        [IStepState.RUNNING]: Colors.accentGrayHover(),
        [IStepState.SUCCEEDED]: Colors.accentGreenHover(),
        [IStepState.SKIPPED]: Colors.accentYellowHover(),
        [IStepState.FAILED]: Colors.accentRedHover(),
        [IStepState.PREPARING]: Colors.accentRedHover(),
        [IStepState.RETRY_REQUESTED]: Colors.accentRedHover(),
        [IStepState.UNKNOWN]: Colors.accentRedHover(),
      })[state]};
  }
`;
