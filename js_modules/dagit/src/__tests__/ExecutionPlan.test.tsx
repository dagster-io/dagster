import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";
import { ExecutionPlan, IExecutionPlanProps } from "../plan/ExecutionPlan";
import { StepKind } from "../types/globalTypes";

it("renders given an execution plan", () => {
  const executionPlanProps: IExecutionPlanProps = {
    executionPlan: {
      __typename: "ExecutionPlan",
      artifactsPersisted: true,
      steps: [
        {
          __typename: "ExecutionStep",
          key: "raw_file_event_admins.compute",
          kind: StepKind.COMPUTE
        }
      ]
    }
  };
  const component = TestRenderer.create(
    <BrowserRouter>
      <ExecutionPlan {...executionPlanProps} />
    </BrowserRouter>
  );
  expect(component.toJSON()).toMatchSnapshot();
});
