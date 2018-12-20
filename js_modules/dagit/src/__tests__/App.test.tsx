import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import App from "../App";
import AppCache from "../AppCache";
import { MockedProvider } from "./MockedProvider";
import MOCKS from "./mockData";

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

  await new Promise(resolve => setTimeout(resolve, 1000));

  const tree = component.toJSON();
  expect(tree).toMatchSnapshot();
}

it("renders without error", async () => {
  await testApp();
});

it("renders pipeline page", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world");
  });
  await testApp();
});

it("renders pipeline solid page", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world/load_num_csv");
  });
  await testApp();
});

it("renders type page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/pandas_hello_world/load_num_csv?types=true"
    );
  });
  await testApp();
});

it("renders type page", async () => {
  beforeEach(() => {
    window.history.pushState(
      {},
      "",
      "/pandas_hello_world/load_num_csv?typeExplorer=PandasDataFrame"
    );
  });
  await testApp();
});

it("renders execution", async () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/pandas_hello_world/execute");
  });
  await testApp();
});
