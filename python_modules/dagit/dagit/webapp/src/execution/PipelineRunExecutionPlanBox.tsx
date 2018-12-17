import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner, Intent } from "@blueprintjs/core";
import { IStepState } from "./StepMetadataProvider";

interface IExecutionPlanBoxProps {
  state: IStepState;
  name: string;
  start: number | undefined;
  elapsed: number | undefined;
  delay: number;
  onShowStateDetails: (stepName: string) => void;
  onApplyStepFilter: (stepName: string) => void;
}

interface IExecutionPlanBoxState {
  v: number;
}

function formatExecutionTime(msec: number) {
  if (msec < 1000) {
    // < 1 second, show msec
    return `${Math.ceil(msec)} msec`;
  } else if (msec < 10 * 1000) {
    // < 10 seconds, show seconds with one decimal point
    return `${Math.ceil(msec / 100) / 10} sec`;
  } else if (msec < 60 * 1000) {
    // < 1 min, show seconds
    return `${Math.ceil(msec / 1000)} sec`;
  } else if (msec < 60 * 60 * 1000) {
    // < 1 hour, show minutes
    return `${Math.ceil(msec / (60 * 1000))} min`;
  } else {
    return `${Math.ceil(msec / (60 * 60 * 1000))} hours`;
  }
}

export class ExecutionPlanBox extends React.Component<
  IExecutionPlanBoxProps,
  IExecutionPlanBoxState
> {
  state = {
    v: 0
  };

  timer?: NodeJS.Timer;

  shouldComponentUpdate(
    nextProps: IExecutionPlanBoxProps,
    nextState: IExecutionPlanBoxState
  ) {
    return (
      nextProps.state !== this.props.state ||
      nextProps.name !== this.props.name ||
      nextProps.elapsed !== this.props.elapsed ||
      nextState.v !== this.state.v
    );
  }

  componentDidMount() {
    this.ensureTimer();
  }

  componentDidUpdate() {
    this.ensureTimer();
  }

  componentWillUnmount() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }
  }

  ensureTimer = () => {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = undefined;
    }

    const { state, start } = this.props;

    // Schedule another update of the component when the elapsed time
    // since the `start` timestamp crosses another 1s boundary.
    if (state === IStepState.RUNNING && start) {
      const nextMs = 1000 - ((Date.now() - start) % 1000);
      this.timer = setTimeout(this.onTick, nextMs);
    }
  };

  onTick = () => {
    // bogus state change to trigger a re-render
    this.setState({ v: this.state.v + 1 });
  };

  render() {
    const {
      state,
      start,
      name,
      delay,
      onApplyStepFilter,
      onShowStateDetails
    } = this.props;

    let elapsed = this.props.elapsed;
    if (state === IStepState.RUNNING && start) {
      elapsed = Math.floor((Date.now() - start) / 1000) * 1000;
      if (elapsed === 0) elapsed = undefined;
    }

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
    transparent 30%,
    rgba(255, 255, 255, 0.7) 65%,
    transparent 68%
  );
  background-size: 150px;
  background-position-x: ${({ success }) =>
    success ? `calc(100% + 150px)` : `-150px`};
  background-repeat: no-repeat;
  pointer-events: none;
  transition: ${({ success }) =>
    success ? "400ms background-position-x linear" : ""};
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
