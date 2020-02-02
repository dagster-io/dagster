import * as React from "react";
import styled from "styled-components/macro";
import gql from "graphql-tag";
import { NonIdealState, Colors, Icon } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";
import { RunPreviewExecutionPlanResultFragment } from "./types/RunPreviewExecutionPlanResultFragment";
import { RunPreviewConfigValidationFragment } from "./types/RunPreviewConfigValidationFragment";
import PythonErrorInfo from "../PythonErrorInfo";
import InfoModal from "../InfoModal";
import { ExecutionPlan } from "../plan/ExecutionPlan";
import { GaantChart, GaantChartMode } from "../gaant/GaantChart";
import { getFeatureFlags, FeatureFlag } from "../Util";

interface IRunPreviewProps {
  plan?: RunPreviewExecutionPlanResultFragment;
  validation?: RunPreviewConfigValidationFragment;
  toolbarActions?: React.ReactChild;
}

interface IRunPreviewState {
  showErrorModal: boolean;
}

interface IErrorMessage {
  message: string | JSX.Element;
}

export class RunPreview extends React.Component<
  IRunPreviewProps,
  IRunPreviewState
> {
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
          ...GaantChartExecutionPlanFragment
        }
        ... on PipelineNotFoundError {
          message
        }
        ... on InvalidSubsetError {
          message
        }
        ...PythonErrorFragment
      }
      ${GaantChart.fragments.GaantChartExecutionPlanFragment}
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `
  };

  state: IRunPreviewState = {
    showErrorModal: false
  };

  shouldComponentUpdate(
    nextProps: IRunPreviewProps,
    nextState: IRunPreviewState
  ) {
    return (
      nextProps.plan !== this.props.plan ||
      nextProps.validation !== this.props.validation ||
      nextState.showErrorModal !== this.state.showErrorModal
    );
  }

  render() {
    const { plan, validation, toolbarActions } = this.props;
    const gaantPreview = getFeatureFlags().includes(
      FeatureFlag.GaantExecutionPlan
    );

    let pythonError = null;
    let errors: IErrorMessage[] = [];
    if (validation?.__typename === "PipelineConfigValidationInvalid") {
      errors = validation.errors;
    }

    if (plan?.__typename === "InvalidSubsetError") {
      errors = [plan];
    }

    if (plan?.__typename === "PythonError") {
      pythonError = plan;
      const message = (
        <>
          PythonError{" "}
          <span
            style={{ cursor: "pointer", textDecoration: "underline" }}
            onClick={() => this.setState({ showErrorModal: true })}
          >
            click for details
          </span>
        </>
      );
      errors = [{ message: message }];
    }

    return plan?.__typename === "ExecutionPlan" ? (
      gaantPreview ? (
        <GaantChart
          plan={plan}
          options={{ mode: GaantChartMode.WATERFALL, hideTimedMode: true }}
          toolbarActions={toolbarActions}
        />
      ) : (
        <>
          <OptionsContainer>
            <div style={{ flex: 1 }} />
            {toolbarActions}
          </OptionsContainer>
          <ExecutionPlan executionPlan={plan} />
        </>
      )
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
        {pythonError && this.state.showErrorModal && (
          <InfoModal
            onRequestClose={() => this.setState({ showErrorModal: false })}
          >
            <PythonErrorInfo error={pythonError} />
          </InfoModal>
        )}
      </NonIdealWrap>
    );
  }
}

const NonIdealWrap = styled.div`
  display: flex;
  flex-direction: column;
  padding: 20px;
  padding-top: 12vh;
  overflow: auto;
`;
const ErrorsWrap = styled.div`
  padding-top: 2vh;
  font-size: 0.9em;
  color: ${Colors.BLACK};
  max-width: 900px;
  margin: auto;
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

const OptionsContainer = styled.div`
  height: 47px;
  display: flex;
  align-items: center;
  padding: 5px 10px;
  border-bottom: 1px solid #A7B6C2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
}`;
