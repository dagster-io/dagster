import {Colors} from '@dagster-io/ui';
import styled from 'styled-components/macro';

import {IStepState} from './RunMetadataProvider';

export const ExecutionStateDot = styled.div<{state: IStepState}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  transition: background 200ms linear;
  background: ${({state}) =>
    ({
      [IStepState.RUNNING]: Colors.Gray400,
      [IStepState.SUCCEEDED]: Colors.Green700,
      [IStepState.SKIPPED]: Colors.Yellow500,
      [IStepState.FAILED]: Colors.Red500,
      [IStepState.PREPARING]: Colors.Red500,
      [IStepState.RETRY_REQUESTED]: Colors.Red500,
      [IStepState.UNKNOWN]: Colors.Red500,
    }[state])};
  &:hover {
    background: ${({state}) =>
      ({
        [IStepState.RUNNING]: Colors.Gray400,
        [IStepState.SUCCEEDED]: Colors.Green700,
        [IStepState.SKIPPED]: Colors.Yellow500,
        [IStepState.FAILED]: Colors.Red200,
        [IStepState.PREPARING]: Colors.Red500,
        [IStepState.RETRY_REQUESTED]: Colors.Red500,
        [IStepState.UNKNOWN]: Colors.Red500,
      }[state])};
  }
`;
