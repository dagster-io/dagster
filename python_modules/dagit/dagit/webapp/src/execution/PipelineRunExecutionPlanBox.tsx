import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner, Intent } from "@blueprintjs/core";
import { IStepState } from "./PipelineRunExecutionPlan";

interface IExecutionPlanBoxProps {
  state: IStepState;
  name: string;
  elapsed: number | undefined;
  delay: number;
  onShowStateDetails: (stepName: string) => void;
  onApplyStepFilter: (stepName: string) => void;
}

function formatExecutionTime(msec: number) {
  if (msec < 100 * 1000) {
    // < 100 seconds, show msec
    return `${Math.ceil(msec)} msec`;
  } else if (msec < 5 * 60 * 1000) {
    // < 5 min, show seconds
    return `${Math.ceil(msec / 1000)} sec`;
  } else if (msec < 120 * 60 * 1000) {
    // < 2 hours, show minutes
    return `${Math.ceil(msec / (60 * 1000))} min`;
  } else {
    return `${Math.ceil(msec / (60 * 60 * 1000))} hours`;
  }
}

export class ExecutionPlanBox extends React.Component<IExecutionPlanBoxProps> {
  shouldComponentUpdate(nextProps: IExecutionPlanBoxProps) {
    return (
      nextProps.state !== this.props.state ||
      nextProps.name !== this.props.name ||
      nextProps.elapsed !== this.props.elapsed
    );
  }
  render() {
    const {
      state,
      name,
      elapsed,
      delay,
      onApplyStepFilter,
      onShowStateDetails
    } = this.props;

    return (
      <ExecutionPlanBoxContainer
        state={state}
        className={state}
        style={{ transitionDelay: `${delay}ms` }}
        onClick={() => onApplyStepFilter(name)}
      >
        <ExecutionFinishedFlash
          style={{ transitionDelay: `${delay}ms` }}
          success={state === IStepState.SUCCEEDED}
        />
        <ExeuctionStateWrap onClick={() => onShowStateDetails(name)}>
          {state === IStepState.RUNNING ? (
            <Spinner intent={Intent.NONE} size={11} />
          ) : (
            <ExecutionStateDot
              state={state}
              style={{ transitionDelay: `${delay}ms` }}
            />
          )}
        </ExeuctionStateWrap>
        <ExecutionPlanBoxName>{name}</ExecutionPlanBoxName>
        {elapsed && (
          <ExecutionStateLabel>
            {formatExecutionTime(elapsed)}
          </ExecutionStateLabel>
        )}
      </ExecutionPlanBoxContainer>
    );
  }
}

const ExeuctionStateWrap = styled.div`
  display: inherit;
  margin-right: 9px;
`;

const ExecutionStateDot = styled.div<{ state: IStepState }>`
  display: inline-block;
  width: 11px;
  height: 11px;
  border-radius: 5.5px;
  transition: background 200ms linear;
  background: ${({ state }) =>
    ({
      [IStepState.WAITING]: Colors.GRAY1,
      [IStepState.RUNNING]: Colors.GRAY3,
      [IStepState.SUCCEEDED]: Colors.GREEN2,
      [IStepState.FAILED]: Colors.RED3
    }[state])};
  &:hover {
    background: ${({ state }) =>
      ({
        [IStepState.WAITING]: Colors.GRAY1,
        [IStepState.RUNNING]: Colors.GRAY3,
        [IStepState.SUCCEEDED]: Colors.GREEN2,
        [IStepState.FAILED]: Colors.RED5
      }[state])};
  }
`;

const ExecutionStateLabel = styled.div`
  opacity: 0.7;
  font-size: 0.9em;
  margin-left: 10px;
`;

const ExecutionPlanBoxName = styled.div`
  font-weight: 500;
`;

const ExecutionFinishedFlash = styled.div<{ success: boolean }>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    111deg,
    transparent 40%,
    rgba(255, 255, 255, 0.4) 65%,
    transparent 68%
  );
  background-size: 200px;
  background-position-x: ${({ success }) => (success ? 180 : -180)}px;
  background-repeat-x: no-repeat;
  transition: ${({ success }) =>
    success ? "300ms background-position-x linear" : ""};
`;

const ExecutionPlanBoxContainer = styled.div<{ state: IStepState }>`
  background: ${({ state }) =>
    state === IStepState.WAITING ? Colors.GRAY3 : Colors.LIGHT_GRAY2}
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
  color: ${Colors.DARK_GRAY3};
  padding: 4px;
  padding-right: 10px;
  margin: 6px;
  margin-left: 15px;
  margin-bottom: 0;
  display: inline-flex;
  min-width: 150px;
  align-items: center;
  border-radius: 3px;
  position: relative;
  z-index: 2;
  transition: background 200ms linear;
  border: 2px solid transparent;
  &:hover {
    cursor: default;
    color: ${Colors.BLACK};
    border: 2px solid ${({ state }) =>
      state === IStepState.WAITING ? Colors.LIGHT_GRAY4 : Colors.WHITE};
  }
`;
