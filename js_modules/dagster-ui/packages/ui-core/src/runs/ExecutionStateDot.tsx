import styled from 'styled-components';

import {
  colorAccentGray,
  colorAccentGrayHover,
  colorAccentGreen,
  colorAccentGreenHover,
  colorAccentRed,
  colorAccentRedHover,
  colorAccentYellow,
  colorAccentYellowHover,
} from '@dagster-io/ui-components';

import {IStepState} from './RunMetadataProvider';

export const ExecutionStateDot = styled.div<{state: IStepState}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  transition: background 200ms linear;
  background: ${({state}) =>
    ({
      [IStepState.RUNNING]: colorAccentGray(),
      [IStepState.SUCCEEDED]: colorAccentGreen(),
      [IStepState.SKIPPED]: colorAccentYellow(),
      [IStepState.FAILED]: colorAccentRed(),
      [IStepState.PREPARING]: colorAccentRed(),
      [IStepState.RETRY_REQUESTED]: colorAccentRed(),
      [IStepState.UNKNOWN]: colorAccentRed(),
    })[state]};
  &:hover {
    background: ${({state}) =>
      ({
        [IStepState.RUNNING]: colorAccentGrayHover(),
        [IStepState.SUCCEEDED]: colorAccentGreenHover(),
        [IStepState.SKIPPED]: colorAccentYellowHover(),
        [IStepState.FAILED]: colorAccentRedHover(),
        [IStepState.PREPARING]: colorAccentRedHover(),
        [IStepState.RETRY_REQUESTED]: colorAccentRedHover(),
        [IStepState.UNKNOWN]: colorAccentRedHover(),
      })[state]};
  }
`;
