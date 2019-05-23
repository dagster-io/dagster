import * as React from "react";
import styled from "styled-components";
import { Colors, Tag, Intent, Divider } from "@blueprintjs/core";
import { DisplayEvent } from "./DisplayEvent";
import { DisclosureTriangle } from "./ExecutionPlanBox";
import {
  IExpectationResult,
  IExpectationResultStatus,
  IMaterialization
} from "./RunMetadataProvider";

interface IDisplayEventsContainerProps {
  expectationResults: IExpectationResult[];
  materializations: IMaterialization[];
}

interface IDisplayEventsContainerState {
  expectationResultsExpanded: boolean;
  materializationsExpanded: boolean;
}

export class DisplayEventsContainer extends React.Component<
  IDisplayEventsContainerProps,
  IDisplayEventsContainerState
> {
  state = {
    expectationResultsExpanded: false,
    materializationsExpanded: true
  };

  render() {
    const { expectationResultsExpanded, materializationsExpanded } = this.state;
    const { expectationResults, materializations } = this.props;

    const hasExpectationResults = expectationResults.length > 0;
    const nExpectationResultsPassed = expectationResults
      .map(e => e.status === IExpectationResultStatus.PASSED)
      .reduce((acc, x) => acc + (x ? 1 : 0), 0);
    const nExpectationResultsFailed = expectationResults
      .map(e => e.status === IExpectationResultStatus.FAILED)
      .reduce((acc, x) => acc + (x ? 1 : 0), 0);
    const hasPassedExpectationResults = nExpectationResultsPassed > 0;
    const hasFailedExpectationResults = nExpectationResultsFailed > 0;

    const hasMaterializations = materializations.length > 0;
    const nMaterializations = materializations.length;

    return (
      <DisplayEventsContainerDiv>
        {hasExpectationResults ? (
          <div>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center"
              }}
            >
              <DisclosureTriangle
                expanded={expectationResultsExpanded}
                onClick={() =>
                  this.setState({
                    expectationResultsExpanded: !expectationResultsExpanded
                  })
                }
              />
              <div style={{ width: 4 }} />
              <span style={{ fontWeight: 500 }}> Expectations</span>&nbsp;
              <Tag
                intent={
                  hasPassedExpectationResults ? Intent.SUCCESS : Intent.NONE
                }
                style={ExpectationsResultTagStyle}
              >
                {nExpectationResultsPassed} passed
              </Tag>
              &nbsp;
              <Tag
                intent={
                  hasFailedExpectationResults ? Intent.DANGER : Intent.NONE
                }
                style={ExpectationsResultTagStyle}
              >
                {nExpectationResultsFailed} failed
              </Tag>
            </div>
            {expectationResultsExpanded && (
              <div>
                {expectationResults.map((e, idx) => (
                  <DisplayEvent event={e} key={`${idx}`} />
                ))}
              </div>
            )}
            <Divider />
          </div>
        ) : (
          ""
        )}
        {hasMaterializations ? (
          <div>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center"
              }}
            >
              <DisclosureTriangle
                expanded={materializationsExpanded}
                onClick={() =>
                  this.setState({
                    materializationsExpanded: !materializationsExpanded
                  })
                }
              />
              <div style={{ width: 4 }} />
              <span style={{ fontWeight: 500 }}> Materializations</span>&nbsp;
              <Tag intent={Intent.NONE} style={ExpectationsResultTagStyle}>
                {nMaterializations} materialized values
              </Tag>
            </div>
            {materializationsExpanded &&
              materializations.map((e, idx) => (
                <DisplayEvent event={e} key={`${idx}`} />
              ))}
          </div>
        ) : (
          ""
        )}
      </DisplayEventsContainerDiv>
    );
  }
}

const DisplayEventsContainerDiv = styled.div`
  color: ${Colors.BLACK};
  border-top: 1px solid rgba(0, 0, 0, 0.15);
  margin-top: 4px;
  padding-left: 16px;
`;

const ExpectationsResultTagStyle = {
  fontSize: "10px",
  minHeight: "10px",
  minWidth: "10px",
  paddingRight: "4px",
  paddingLeft: "4px",
  paddingTop: "0px",
  paddingBottom: "0px"
};
