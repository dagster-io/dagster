import * as React from 'react';
import * as TestRenderer from 'react-test-renderer';

import {App} from 'src/App';
import {AppCache} from 'src/AppCache';
import {PipelineGraphContainer} from 'src/graph/PipelineGraphContainer';
import {MOCKS} from 'src/testing/AppMocks';
import {MockedProvider} from 'src/testing/MockedProvider';

function createNodeMock(element: any) {
  if (element.type === 'div') {
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
          height: 1000,
        };
      },
    };
  }
  return null;
}

async function testApp() {
  let component: TestRenderer.ReactTestRenderer;
  await TestRenderer.act(async () => {
    component = TestRenderer.create(
      <MockedProvider mocks={MOCKS} addTypename={true} cache={AppCache}>
        <App />
      </MockedProvider>,
      {createNodeMock},
    );
    // wait for the graphql promises to settle. Usually one tick is enough for us,
    // except when a query resolves and triggers another query lower in the tree.
    await new Promise((resolve) => setTimeout(resolve, 1000));
  });

  const tree = component!.toJSON();
  expect(tree).toMatchSnapshot();
  return component!.root;
}

// [dish] Possibly temporary -- let's come back to this once we have the newer testing pieces
// in place.
jest.useRealTimers();

it('renders without error', async () => {
  await testApp();
});

it('renders pipeline page', async () => {
  window.history.pushState({}, '', '/pipelines/airline_demo_ingest_pipeline');
  const app = await testApp();

  // Sanity check that the pipeline page actually rendered the graph container. This ensures
  // we don't accidentally update the snapshots to a "correct" state that is loading / broken.
  const graphEls = app.findAllByType(PipelineGraphContainer, {deep: true});
  expect(graphEls.length).toBe(1);
});

it('renders pipeline solid page', async () => {
  window.history.pushState(
    {},
    '',
    '/pipelines/airline_demo_ingest_pipeline/download_q2_sfo_weather',
  );
  await testApp();
});

it('renders type page', async () => {
  window.history.pushState(
    {},
    '',
    '/pipelines/airline_demo_ingest_pipeline/download_q2_sfo_weather?types=true',
  );
  await testApp();
});

it('renders type page', async () => {
  window.history.pushState(
    {},
    '',
    '/pipelines/airline_demo_ingest_pipeline/download_q2_sfo_weather?typeExplorer=PySparkDataFrame',
  );
  await testApp();
});

it('renders solids explorer', async () => {
  window.history.pushState({}, '', '/solids/s3_to_df');
  await testApp();
});

it('renders execution', async () => {
  window.history.pushState({}, '', '/pipeline/airline_demo_ingest_pipeline/playground');
  await testApp();
});
