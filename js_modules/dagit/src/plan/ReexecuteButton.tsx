import * as React from "react";
import styled from "styled-components/macro";
import { Icon } from "@blueprintjs/core";
import { IStepState } from "../RunMetadataProvider";
import { IconNames } from "@blueprintjs/icons";

interface ReexecuteButtonProps {
  stepKey: string;
  state: IStepState;
  executionArtifactsPersisted: boolean;
  onReexecuteStep?: (stepKey: string) => void;
}

export function ReexecuteButton(props: ReexecuteButtonProps) {
  const {
    onReexecuteStep,
    state,
    executionArtifactsPersisted,
    stepKey
  } = props;

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
      style={{ border: `1px solid white` }}
      onClick={() => onReexecuteStep(stepKey)}
    >
      <Icon icon={IconNames.PLAY} iconSize={15} />
    </ReExecuteContainer>
  );
}

const ReExecuteContainer = styled.div`
  display: inline-block;
  margin: 0 5px 0 3px;
  border-radius: 13px;
  width: 19px;
  height: 19px;
  padding: 1px 2px;
`;
