import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { App } from "../App";
import AppCache from "../AppCache";
import { MOCKS } from "./AppMocks";
import { MockedProvider } from "./MockedProvider";

function createNodeMock(element: any) {
  if (element.type === "div") {
    return {
      querySelector() {
        return null;
      },
      querySelectorAll() {
        return [];
      },
      getBoundingClientRect() {
        return {
          left: 0,
          top: 0,
          right: 1000,
          bottom: 1000,
          x: 0,
          y: 0,
          width: 1000,
          height: 1000
        };
      }
    };
  }
  return null;
}

async function testApp() {
  const component = TestRenderer.create(
    <MockedProvider mocks={MOCKS} addTypename={true} cache={AppCache}>
      <App />
    </MockedProvider>,
    { createNodeMock }
  );

  // wait for the graphql promises to settle. Usually one tick is enough for us,
  // except when a query resolves and triggers another query lower in the tree.
  await new Promise(resolve => setTimeout(resolve, 1000));

  const tree = component.toJSON();
  expect(tree).toMatchSnapshot();
}

it("renders without error", async () => {
  await testApp();
});

it("renders pipeline page", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/p/airline_demo_ingest_pipeline/explore");
  });
  await testApp();
});

it("renders pipeline solid page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/p/airline_demo_ingest_pipeline/explore/download_q2_sfo_weather"
    );
  });
  await testApp();
});

it("renders type page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/p/airline_demo_ingest_pipeline/explore/download_q2_sfo_weather?types=true"
    );
  });
  await testApp();
});

it("renders type page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/p/airline_demo_ingest_pipeline/explore/download_q2_sfo_weather?typeExplorer=PandasDataFrame"
    );
  });
  await testApp();
});

it("renders solids explorer", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/solids/s3_to_df");
  });
  await testApp();
});

it("renders execution", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/p/airline_demo_ingest_pipeline/execute");
  });
  await testApp();
});
