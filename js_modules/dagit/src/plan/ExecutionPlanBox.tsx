import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner, Intent } from "@blueprintjs/core";
import {
  IExpectationResult,
  IMaterialization,
  IStepState
} from "../RunMetadataProvider";
import { DisplayEvents } from "./DisplayEvents";
import { formatElapsedTime } from "../Util";
import { ReexecuteButton } from "./ReexecuteButton";

export interface IExecutionPlanBoxProps {
  state: IStepState;
  stepKey: string;
  start: number | undefined;
  elapsed: number | undefined;
  delay: number;
  materializations: IMaterialization[];
  expectationResults: IExpectationResult[];
  onShowStateDetails?: (stepName: string) => void;
  onApplyStepFilter?: (stepName: string) => void;
  executionArtifactsPersisted: boolean;
  onReexecuteStep?: (stepKey: string) => void;
}

export interface IExecutionPlanBoxState {
  expanded: boolean;
  v: number;
}

export class ExecutionPlanBox extends React.Component<
  IExecutionPlanBoxProps,
  IExecutionPlanBoxState
> {
  state = {
    expanded: false,
    v: 0
  };

  timer?: NodeJS.Timer;

  shouldComponentUpdate(
    nextProps: IExecutionPlanBoxProps,
    nextState: IExecutionPlanBoxState
  ) {
    return (
      nextProps.state !== this.props.state ||
      nextProps.stepKey !== this.props.stepKey ||
      nextProps.elapsed !== this.props.elapsed ||
      nextState.expanded !== this.state.expanded ||
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
      stepKey: stepKey,
      delay,
      expectationResults,
      materializations,
      onApplyStepFilter,
      onReexecuteStep,
      onShowStateDetails,
      executionArtifactsPersisted
    } = this.props;

    const { expanded } = this.state;

    let elapsed = this.props.elapsed;
    if (state === IStepState.RUNNING && start) {
      elapsed = Math.floor((Date.now() - start) / 1000) * 1000;
    }

    return (
      <>
        <ExecutionPlanRowContainer>
          <ExecutionPlanBoxContainer
            state={state}
            className={state}
            style={{ transitionDelay: `${delay}ms` }}
            onClick={() => onApplyStepFilter && onApplyStepFilter(stepKey)}
          >
            <ExecutionFinishedFlash
              style={{ transitionDelay: `${delay}ms` }}
              success={state === IStepState.SUCCEEDED}
            />
            <div
              style={{
                display: "inline-flex",
                alignItems: "center"
              }}
            >
              <ExecutionStateWrap
                onClick={() =>
                  onShowStateDetails && onShowStateDetails(stepKey)
                }
              >
                {state === IStepState.RUNNING ? (
                  <Spinner intent={Intent.NONE} size={11} />
                ) : (
                  <ExecutionStateDot
                    state={state}
                    title={`${state[0].toUpperCase()}${state.substr(1)}`}
                    style={{ transitionDelay: `${delay}ms` }}
                  />
                )}
                <div style={{ width: 4 }} />
                {(expectationResults.length > 0 ||
                  materializations.length > 0) && (
                  <DisclosureTriangle
                    onClick={() => this.setState({ expanded: !expanded })}
                    expanded={expanded}
                  />
                )}
              </ExecutionStateWrap>
              <ExecutionPlanBoxName title={stepKey}>
                {stepKey}
              </ExecutionPlanBoxName>
              {elapsed !== undefined && <ExecutionTime elapsed={elapsed} />}
            </div>
            {expanded && (
              <DisplayEvents
                materializations={materializations}
                expectationResults={expectationResults}
              />
            )}
          </ExecutionPlanBoxContainer>
          <ReexecuteButton
            onReexecuteStep={onReexecuteStep}
            state={state}
            executionArtifactsPersisted={executionArtifactsPersisted}
            stepKey={stepKey}
          />
        </ExecutionPlanRowContainer>
      </>
    );
  }
}

const ExecutionStateWrap = styled.div`
  display: flex;
  margin-right: 5px;
  align-items: center;
`;

export const DisclosureTriangle = styled.div<{ expanded: boolean }>`
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 8px solid rgba(0, 0, 0, 0.5);
  transition: transform 150ms linear;
  transform: ${({ expanded }) =>
    expanded ? "rotate(0deg)" : "rotate(-90deg)"};
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
      [IStepState.SKIPPED]: Colors.GOLD3,
      [IStepState.FAILED]: Colors.RED3
    }[state])};
  &:hover {
    background: ${({ state }) =>
      ({
        [IStepState.WAITING]: Colors.GRAY1,
        [IStepState.RUNNING]: Colors.GRAY3,
        [IStepState.SUCCEEDED]: Colors.GREEN2,
        [IStepState.SKIPPED]: Colors.GOLD3,
        [IStepState.FAILED]: Colors.RED5
      }[state])};
  }
`;

const ExecutionTime = ({ elapsed }: { elapsed: number }) => {
  let text = formatElapsedTime(elapsed);
  // Note: Adding a min-width prevents the size of the execution plan box from
  // shifting /slightly/ as the elapsed time increments.
  return (
    <ExecutionTimeContainer style={{ minWidth: text.length * 6.8 }}>
      {text}
    </ExecutionTimeContainer>
  );
};

const ExecutionTimeContainer = styled.div`
  opacity: 0.7;
  font-size: 0.9em;
  margin-left: 10px;
`;

const ExecutionPlanBoxName = styled.div`
  font-weight: 500;
  text-overflow: ellipsis;
  overflow: hidden;
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

const ExecutionPlanRowContainer = styled.div`
  display: flex;
  align-items: center;

  .reexecute {
    opacity: 0;
  }
  &:hover {
    .reexecute {
      opacity: 0.5;
    }
    .reexecute:hover {
      opacity: 1;
    }
  }
`;

const ExecutionPlanBoxContainer = styled.div<{ state: IStepState }>`
  background: ${({ state }) =>
    state === IStepState.WAITING ? Colors.GRAY3 : Colors.LIGHT_GRAY2}
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
  color: ${Colors.DARK_GRAY3};
  padding: 4px;
  padding-right: 10px;
  margin: 3px;
  margin-left: 12px;
  border-radius: 3px;
  min-width: 150px;
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
