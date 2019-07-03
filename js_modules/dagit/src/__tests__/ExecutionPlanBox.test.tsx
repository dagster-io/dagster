import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";
import {
  ExecutionPlanBox,
  IExecutionPlanBoxProps,
  IExecutionPlanBoxState
} from "../plan/ExecutionPlanBox";
import {
  IExpectationResult,
  IExpectationResultStatus,
  IMaterialization,
  IStepState,
  IStepDisplayIconType,
  IStepDisplayActionType
} from "../RunMetadataProvider";

it("renders given materializations and passing expectations", () => {
  const tables = [
    "users",
    "groups",
    "events",
    "friends",
    "pages",
    "fans",
    "event_admins",
    "group_admins"
  ];

  const expectationResults: IExpectationResult[] = tables.map(table => ({
    icon: IStepDisplayIconType.SUCCESS,
    items: [],
    status: IExpectationResultStatus.PASSED,
    text: table + ".row_count"
  }));

  const materializations: IMaterialization[] = tables.map(table => ({
    icon: IStepDisplayIconType.LINK,
    text: table,
    items: [
      {
        action: IStepDisplayActionType.COPY,
        actionText: "[Copy Path]",
        actionValue: "/path/to/" + table,
        text: table
      }
    ]
  }));

  const executionPlanBoxProps: IExecutionPlanBoxProps = {
    delay: 200,
    elapsed: 21,
    executionArtifactsPersisted: false,
    expectationResults: expectationResults,
    materializations: [],
    stepKey: "many_materializations_and_passing_expectations",
    state: IStepState.SUCCEEDED,
    start: 1558389791907
  };

  const executionPlanBoxStateExpanded: IExecutionPlanBoxState = {
    expanded: true,
    v: 0
  };

  const component = TestRenderer.create(
    <BrowserRouter>
      <ExecutionPlanBox {...executionPlanBoxProps} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
  component.root.instance.setState(executionPlanBoxStateExpanded);
  expect(component.toJSON()).toMatchSnapshot();
});
