import * as React from "react";
import styled from "styled-components";
import gql from "graphql-tag";
import { NonIdealState, Colors, Icon } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { ExecutionPlan } from "../plan/ExecutionPlan";
import { RunPreviewExecutionPlanResultFragment } from "./types/RunPreviewExecutionPlanResultFragment";
import { RunPreviewConfigValidationFragment } from "./types/RunPreviewConfigValidationFragment";

interface IRunPreviewProps {
  plan?: RunPreviewExecutionPlanResultFragment;
  validation?: RunPreviewConfigValidationFragment;
}

interface IErrorMessage {
  message: string;
}

export class RunPreview extends React.Component<IRunPreviewProps> {
  static fragments = {
    RunPreviewConfigValidationFragment: gql`
      fragment RunPreviewConfigValidationFragment on PipelineConfigValidationResult {
        __typename
        ... on PipelineConfigValidationInvalid {
          errors {
            reason
            message
          }
        }
      }
    `,
    RunPreviewExecutionPlanResultFragment: gql`
      fragment RunPreviewExecutionPlanResultFragment on ExecutionPlanResult {
        __typename
        ... on ExecutionPlan {
          ...ExecutionPlanFragment
        }
        ... on PipelineNotFoundError {
          message
        }
        ... on InvalidSubsetError {
          message
        }
      }
      ${ExecutionPlan.fragments.ExecutionPlanFragment}
    `
  };

  render() {
    const { plan, validation } = this.props;

    let errors: IErrorMessage[] = [];
    if (
      validation &&
      validation.__typename === "PipelineConfigValidationInvalid"
    ) {
      errors = validation.errors;
    }

    if (plan && plan.__typename === "InvalidSubsetError") {
      errors = [plan];
    }

    return plan && plan.__typename === "ExecutionPlan" ? (
      <ExecutionPlan executionPlan={plan} />
    ) : (
      <NonIdealWrap>
        <NonIdealState
          icon={IconNames.SEND_TO_GRAPH}
          title="No Execution Plan"
          description={
            errors.length
              ? `Fix the ${errors.length.toLocaleString()} ${
                  errors.length === 1 ? "error" : "errors"
                } below to preview the execution plan.`
              : `Provide valid configuration to see an execution plan.`
          }
        />
        <ErrorsWrap>
          {errors.map((e, idx) => (
            <ErrorRow key={idx}>
              <div style={{ paddingRight: 8 }}>
                <Icon icon="error" iconSize={14} color={Colors.RED4} />
              </div>
              {e.message}
            </ErrorRow>
          ))}
        </ErrorsWrap>
      </NonIdealWrap>
    );
  }
}

const NonIdealWrap = styled.div`
  display: flex;
  flex-direction: column;
  padding: 20px;
  padding-top: 12vh;
  overflow: scroll;
`;
const ErrorsWrap = styled.div`
  padding-top: 2vh;
  font-size: 0.9em;
  color: ${Colors.BLACK};
`;

const ErrorRow = styled.div`
  text-align: left;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  background: #eee;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  margin-bottom: 8px;
`;
