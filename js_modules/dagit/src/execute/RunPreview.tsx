import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors, Icon, Checkbox } from "@blueprintjs/core";
import PythonErrorInfo from "../PythonErrorInfo";
import { showCustomAlert } from "../CustomAlertProvider";
import {
  ValidationResult,
  ValidationError
} from "../configeditor/codemirror-yaml/mode";
import {
  ConfigEditorEnvironmentSchemaFragment,
  ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType
} from "../configeditor/types/ConfigEditorEnvironmentSchemaFragment";
import { RunPreviewExecutionPlanResultFragment } from "./types/RunPreviewExecutionPlanResultFragment";
import { SplitPanelContainer } from "../SplitPanelContainer";
import { ButtonLink } from "../ButtonLink";

interface RunPreviewProps {
  plan: RunPreviewExecutionPlanResultFragment | null;
  validationResult: ValidationResult | null;

  actions?: React.ReactChild;
  environmentSchema: ConfigEditorEnvironmentSchemaFragment;
  onHighlightValidationError: (error: ValidationError) => void;
}

interface RunPreviewState {
  errorsOnly: boolean;
}

export class RunPreview extends React.Component<
  RunPreviewProps,
  RunPreviewState
> {
  static fragments = {
    RunPreviewExecutionPlanResultFragment: gql`
      fragment RunPreviewExecutionPlanResultFragment on ExecutionPlanResult {
        __typename
        ... on ExecutionPlan {
          __typename
        }
        ... on PipelineNotFoundError {
          message
        }
        ... on InvalidSubsetError {
          message
        }
        ...PythonErrorFragment
      }
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `
  };

  state: RunPreviewState = {
    errorsOnly: false
  };

  shouldComponentUpdate(
    nextProps: RunPreviewProps,
    nextState: RunPreviewState
  ) {
    return (
      nextProps.validationResult !== this.props.validationResult ||
      nextProps.plan !== this.props.plan ||
      nextState.errorsOnly !== this.state.errorsOnly
    );
  }

  getRootCompositeChildren = () => {
    const {
      allConfigTypes,
      rootEnvironmentType
    } = this.props.environmentSchema;
    const children: {
      [fieldName: string]: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType;
    } = {};

    const root = allConfigTypes.find(t => t.key === rootEnvironmentType.key);
    if (root?.__typename !== "CompositeConfigType") return children;

    root.fields.forEach(field => {
      const allConfigVersion = allConfigTypes.find(
        t => t.key === field.configTypeKey
      );
      if (allConfigVersion?.__typename !== "CompositeConfigType") return;
      children[field.name] = allConfigVersion;
    });

    return children;
  };

  render() {
    const {
      plan,
      actions,
      validationResult,
      onHighlightValidationError
    } = this.props;
    const { errorsOnly } = this.state;

    const errors: (ValidationError | React.ReactNode)[] = [];
    const errorsByNode: { [path: string]: ValidationError[] } = {};

    if (validationResult && !validationResult.isValid) {
      validationResult.errors.forEach(e => {
        errors.push(e);

        const path: string[] = [];
        for (const component of e.path) {
          path.push(component);
          const key = path.join(".");
          errorsByNode[key] = errorsByNode[key] || [];
          errorsByNode[key].push(e);
        }
      });
    }

    if (plan?.__typename === "InvalidSubsetError") {
      errors.push(plan.message);
    }

    if (plan?.__typename === "PythonError") {
      const info = <PythonErrorInfo error={plan} />;
      errors.push(
        <>
          PythonError{" "}
          <span onClick={() => showCustomAlert({ body: info })}>
            click for details
          </span>
        </>
      );
    }

    const { resources, solids, ...rest } = this.getRootCompositeChildren();

    const itemsIn = (parents: string[], names: string[]) => {
      const boxes = names
        .map(name => {
          const path = [...parents, name];
          const errors = errorsByNode[path.join(".")];
          const present = pathExistsInObject(path, validationResult?.document);
          if (errorsOnly && !errors) {
            return false;
          }
          return (
            <Item
              key={name}
              isPresent={present}
              isInvalid={!!errors}
              onClick={() =>
                onHighlightValidationError(
                  errors ? errors[0] : { path, message: "", reason: "" }
                )
              }
            >
              {name}
            </Item>
          );
        })
        .filter(Boolean);

      if (!boxes.length) {
        return <ItemsEmptyNotice>Nothing to display.</ItemsEmptyNotice>;
      }
      return boxes;
    };

    return (
      <SplitPanelContainer
        identifier="run-preview"
        axis="horizontal"
        first={
          <ErrorListContainer>
            <Section>
              <SectionTitle>Errors</SectionTitle>
              {errors.map((e, idx) => (
                <ErrorRow
                  key={idx}
                  error={e}
                  onClick={onHighlightValidationError}
                />
              ))}
            </Section>
          </ErrorListContainer>
        }
        firstInitialPercent={50}
        firstMinSize={150}
        second={
          <>
            <div style={{ overflowY: "scroll", width: "100%", height: "100%" }}>
              <RuntimeAndResourcesSection>
                <Section>
                  <SectionTitle>Runtime</SectionTitle>
                  <ItemSet>{itemsIn([], Object.keys(rest))}</ItemSet>
                </Section>
                {(resources?.fields.length || 0) > 0 && (
                  <Section>
                    <SectionTitle>Resources</SectionTitle>
                    <ItemSet>
                      {itemsIn(
                        ["resources"],
                        (resources?.fields || []).map(f => f.name)
                      )}
                    </ItemSet>
                  </Section>
                )}
              </RuntimeAndResourcesSection>
              <Section>
                <SectionTitle>Solids</SectionTitle>
                <ItemSet>
                  {itemsIn(
                    ["solids"],
                    (solids?.fields || []).map(f => f.name)
                  )}
                </ItemSet>
              </Section>
              <div style={{ height: 50 }} />
            </div>
            <div
              style={{
                position: "absolute",
                top: 0,
                right: 0,
                padding: "12px 15px 0px 10px",
                background: "rgba(255,255,255,0.7)"
              }}
            >
              <Checkbox
                label="Errors Only"
                checked={errorsOnly}
                onChange={() => this.setState({ errorsOnly: !errorsOnly })}
              />
            </div>
            <div style={{ position: "absolute", bottom: 14, right: 14 }}>
              {actions}
            </div>
          </>
        }
      />
    );
  }
}

const SectionTitle = styled.div`
  color: ${Colors.GRAY3};
  text-transform: uppercase;
  font-size: 12px;
`;

const Section = styled.div`
  margin-top: 14px;
  margin-left: 10px;
`;

const ItemSet = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
`;

const ItemsEmptyNotice = styled.div`
  font-size: 13px;
  padding-top: 7px;
  padding-bottom: 7px;
`;

const Item = styled.div<{ isInvalid: boolean; isPresent: boolean }>`
  white-space: nowrap;
  font-size: 13px;
  color: ${({ isInvalid }) => (isInvalid ? Colors.WHITE : Colors.BLACK)};
  background: ${({ isInvalid, isPresent }) =>
    isInvalid ? Colors.RED5 : isPresent ? "#C8E1F4" : Colors.LIGHT_GRAY4};
  border-radius: 3px;
  border: 1px solid
    ${({ isPresent, isInvalid }) =>
      isInvalid ? "#CE1126" : isPresent ? "#AFCCE1" : Colors.LIGHT_GRAY2};
  padding: 3px 5px;
  margin: 3px;
  transition: background 150ms linear, color 150ms linear;
  cursor: ${({ isPresent }) => (isPresent ? "default" : "not-allowed")};

  &:hover {
    transition: none;
    background: ${({ isInvalid, isPresent }) =>
      isInvalid ? "#E15858" : isPresent ? "#AFCCE1" : Colors.LIGHT_GRAY4};
  }
`;

const ErrorListContainer = styled.div`
  margin-left: 10px;
  overflow-y: scroll;
  height: 100%;
`;

const ErrorRowContainer = styled.div<{ hoverable: boolean }>`
  text-align: left;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  border-bottom: 1px solid #ccc;
  padding: 7px 0;
  padding-right: 7px;
  margin-bottom: 8px;
  &:last-child {
    border-bottom: 0;
    margin-bottom: 15px;
  }
  ${({ hoverable }) =>
    hoverable &&
    `&:hover {
      background: ${Colors.LIGHT_GRAY5};
    }
  `}
`;

const RuntimeAndResourcesSection = styled.div`
  display: flex;
  @media (max-width: 800px) {
    flex-direction: column;
  }
`;

const ErrorRow: React.FunctionComponent<{
  error: ValidationError | React.ReactNode;
  onClick: (error: ValidationError) => void;
}> = ({ error, onClick }) => {
  let message = error;
  let target: ValidationError | null = null;
  if (error && typeof error === "object" && "message" in error) {
    message = error.message;
    target = error;
  }

  let displayed = message;
  if (typeof message === "string" && message.length > 400) {
    displayed = truncateErrorMessage(message);
  }

  return (
    <ErrorRowContainer
      hoverable={!!target}
      onClick={() => target && onClick(target)}
    >
      <div style={{ paddingRight: 8 }}>
        <Icon icon="error" iconSize={14} color={Colors.RED4} />
      </div>
      <div>
        {displayed}
        {displayed !== message && (
          <>
            &nbsp;
            <ButtonLink
              onClick={() =>
                showCustomAlert({
                  body: <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
                })
              }
            >
              View&nbsp;All&nbsp;&gt;
            </ButtonLink>
          </>
        )}
      </div>
    </ErrorRowContainer>
  );
};

function truncateErrorMessage(message: string) {
  let split = message.indexOf("{");
  if (split === -1) {
    split = message.indexOf(". ");
  }
  if (split === -1) {
    split = 400;
  }
  return message.substr(0, split) + "... ";
}

function pathExistsInObject(path: string[], object: any): boolean {
  if (!object || typeof object !== "object") return false;
  if (path.length === 0) return true;
  const [first, ...rest] = path;
  return pathExistsInObject(rest, object[first]);
}
