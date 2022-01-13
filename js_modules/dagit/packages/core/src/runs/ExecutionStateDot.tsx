import {ColorsWIP} from '@dagster-io/ui';
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
      [IStepState.RUNNING]: ColorsWIP.Gray400,
      [IStepState.SUCCEEDED]: ColorsWIP.Green700,
      [IStepState.SKIPPED]: ColorsWIP.Yellow500,
      [IStepState.FAILED]: ColorsWIP.Red500,
      [IStepState.PREPARING]: ColorsWIP.Red500,
      [IStepState.RETRY_REQUESTED]: ColorsWIP.Red500,
      [IStepState.UNKNOWN]: ColorsWIP.Red500,
    }[state])};
  &:hover {
    background: ${({state}) =>
      ({
        [IStepState.RUNNING]: ColorsWIP.Gray400,
        [IStepState.SUCCEEDED]: ColorsWIP.Green700,
        [IStepState.SKIPPED]: ColorsWIP.Yellow500,
        [IStepState.FAILED]: ColorsWIP.Red200,
        [IStepState.PREPARING]: ColorsWIP.Red500,
        [IStepState.RETRY_REQUESTED]: ColorsWIP.Red500,
        [IStepState.UNKNOWN]: ColorsWIP.Red500,
      }[state])};
  }
`;
