import * as React from "react";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { IStepState } from "../RunMetadataProvider";

export interface IExecutionPlanHiddenStepsBoxProps {
  numberStepsSkipped: number;
}

export class ExecutionPlanHiddenStepsBox extends React.Component<
  IExecutionPlanHiddenStepsBoxProps
  > {
  shouldComponentUpdate(nextProps: IExecutionPlanHiddenStepsBoxProps) {
    return nextProps.numberStepsSkipped !== this.props.numberStepsSkipped;
  }

  render() {
    const { numberStepsSkipped } = this.props;

    return (
      <>
        <ExecutionPlanRowContainer>
          <ExecutionPlanBoxContainer
            state={IStepState.SKIPPED}
            className={IStepState.SKIPPED}
          >
            <div
              style={{
                display: "inline-flex",
                alignItems: "center"
              }}
            >
              <ExecutionStateWrap>
                <div style={{ width: 4 }} />
              </ExecutionStateWrap>
              <ExecutionPlanBoxName
                title={`${numberStepsSkipped} steps hidden`}
              >
                {`${numberStepsSkipped} steps hidden`}
              </ExecutionPlanBoxName>
            </div>
          </ExecutionPlanBoxContainer>
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

const ExecutionPlanBoxName = styled.div`
  font-weight: 500;
  text-overflow: ellipsis;
  overflow: hidden;
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
  background: ${Colors.DARK_GRAY4}
  box-shadow: 0 2px 3px rgba(0, 0, 0, 0.3);
  color: ${Colors.LIGHT_GRAY1};
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
