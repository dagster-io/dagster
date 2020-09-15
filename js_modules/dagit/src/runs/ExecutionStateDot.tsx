import styled from 'styled-components/macro';
import {Colors} from '@blueprintjs/core';
import {IStepState} from '../RunMetadataProvider';

export const ExecutionStateDot = styled.div<{state: IStepState}>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  transition: background 200ms linear;
  background: ${({state}) =>
    ({
      [IStepState.RUNNING]: Colors.GRAY3,
      [IStepState.SUCCEEDED]: Colors.GREEN2,
      [IStepState.SKIPPED]: Colors.GOLD3,
      [IStepState.FAILED]: Colors.RED3,
    }[state])};
  &:hover {
    background: ${({state}) =>
      ({
        [IStepState.RUNNING]: Colors.GRAY3,
        [IStepState.SUCCEEDED]: Colors.GREEN2,
        [IStepState.SKIPPED]: Colors.GOLD3,
        [IStepState.FAILED]: Colors.RED5,
      }[state])};
  }
`;
