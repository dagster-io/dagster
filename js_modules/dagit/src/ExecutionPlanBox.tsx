import * as React from "react";
import styled from "styled-components";
import { Colors, Spinner, Intent, Icon } from "@blueprintjs/core";
import { IStepState, IStepMaterialization } from "./RunMetadataProvider";
import { Materialization } from "./Materialization";
import { formatElapsedTime } from "./Util";
import { IconNames } from "@blueprintjs/icons";

interface IExecutionPlanBoxProps {
  state: IStepState;
  name: string;
  start: number | undefined;
  elapsed: number | undefined;
  delay: number;
  materializations: IStepMaterialization[];
  onShowStateDetails?: (stepName: string) => void;
  onApplyStepFilter?: (stepName: string) => void;
  executionArtifactsPersisted: boolean;
  onReexecuteStep?: (stepName: string) => void;
}

interface ReexecuteButtonProps {
  name: string;
  state: IStepState;
  executionArtifactsPersisted: boolean;
  onReexecuteStep?: (stepName: string) => void;
}

interface IExecutionPlanBoxState {
  v: number;
}

function ReexecuteButton(props: ReexecuteButtonProps) {
  const { onReexecuteStep, state, executionArtifactsPersisted, name } = props;

  // If callback isnt provided, or the step does not fail or succeed - dont render anything
  if (
    !(
      onReexecuteStep &&
      [IStepState.FAILED, IStepState.SUCCEEDED].includes(state)
    )
  ) {
    return null;
  }

  // if execution artifacts are not persisted, we can reexecute but we want to communicate
  // that we could if configuration was changed
  if (!executionArtifactsPersisted) {
    return (
      <ReExecuteContainer
        className="reexecute"
        title="Use a persisting storage mode such as 'filesystem' to enable single step re-execution"
      >
        <Icon icon={IconNames.DISABLE} iconSize={15} />
      </ReExecuteContainer>
    );
  }

  return (
    <ReExecuteContainer
      className="reexecute"
      title="Re-run just this step with existing configuration."
      onClick={() => onReexecuteStep(name)}
    >
      <Icon icon={IconNames.PLAY} iconSize={15} />
    </ReExecuteContainer>
  );
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
      materializations,
      onApplyStepFilter,
      onReexecuteStep,
      onShowStateDetails,
      executionArtifactsPersisted
    } = this.props;

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
            onClick={() => onApplyStepFilter && onApplyStepFilter(name)}
          >
            <ExecutionFinishedFlash
              style={{ transitionDelay: `${delay}ms` }}
              success={state === IStepState.SUCCEEDED}
            />
            <ExeuctionStateWrap
              onClick={() => onShowStateDetails && onShowStateDetails(name)}
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
            </ExeuctionStateWrap>
            <ExecutionPlanBoxName title={name}>{name}</ExecutionPlanBoxName>
            {elapsed !== undefined && <ExecutionTime elapsed={elapsed} />}
          </ExecutionPlanBoxContainer>
          <ReexecuteButton
            onReexecuteStep={onReexecuteStep}
            state={state}
            executionArtifactsPersisted={executionArtifactsPersisted}
            name={name}
          />
        </ExecutionPlanRowContainer>
        {(materializations || []).map(mat => (
          <Materialization
            fileLocation={mat.fileLocation}
            fileName={mat.fileName}
          />
        ))}
      </>
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

const ReExecuteContainer = styled.div`
  display: inline-block;
  border: 1px solid white;
  margin: 0 5px 0 3px;
  border-radius: 13px;
  width: 19px;
  height: 19px;
  padding: 1px 2px;
`;

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
  width: 100%;
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
