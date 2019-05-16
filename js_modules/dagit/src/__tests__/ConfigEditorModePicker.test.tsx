import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import ConfigEditorModePicker from "../execute/ConfigEditorModePicker";
import { PipelineExecutionContainerFragment } from "../execute/types/PipelineExecutionContainerFragment";

it("renders single mode pipelines", () => {
  const singleModePipelineData: PipelineExecutionContainerFragment = {
    __typename: "Pipeline",
    configTypes: [],
    environmentType: {
      __typename: "CompositeConfigType",
      key: "SingleModePipeline.Mode.Default.Environment"
    },
    modes: [
      {
        __typename: "Mode",
        description: null,
        name: "default"
      }
    ],
    name: "single_mode_pipeline"
  };
  const componentNullSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        pipeline={singleModePipelineData}
        modeName={null}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentNullSelected.toJSON()).toMatchSnapshot();

  const componentDefaultSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        pipeline={singleModePipelineData}
        modeName={"default"}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentDefaultSelected.toJSON()).toMatchSnapshot();
});

it("renders multi mode pipelines", () => {
  const multiModePipelineData: PipelineExecutionContainerFragment = {
    __typename: "Pipeline",
    configTypes: [],
    environmentType: {
      __typename: "CompositeConfigType",
      key: "MultiModePipeline.Mode.Default.Environment"
    },
    modes: [
      {
        __typename: "Mode",
        description: "Mode 1",
        name: "mode_1"
      },
      {
        __typename: "Mode",
        description: "Mode 2",
        name: "mode_2"
      }
    ],
    name: "multi_mode_pipeline"
  };
  const componentNullSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        pipeline={multiModePipelineData}
        modeName={null}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentNullSelected.toJSON()).toMatchSnapshot();

  const componentMode1Selected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        pipeline={multiModePipelineData}
        modeName={"mode1"}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentMode1Selected.toJSON()).toMatchSnapshot();
});
