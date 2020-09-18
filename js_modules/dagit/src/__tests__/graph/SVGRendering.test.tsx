import fs from 'fs';
import path from 'path';

import {Colors} from '@blueprintjs/core';
import pretty from 'pretty';
import * as React from 'react';
import * as ReactDOM from 'react-dom/server';
import {StyleSheetManager} from 'styled-components/macro';

import {PipelineGraphContents} from '../../graph/PipelineGraph';
import {getDagrePipelineLayout} from '../../graph/getFullSolidLayout';
import {PipelineGraphSolidFragment} from '../../graph/types/PipelineGraphSolidFragment';
import {PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot} from '../../types/PipelineExplorerRootQuery';

import {MOCKS} from './SVGMocks';

const snapshotsDir = path.join(__dirname, '__snapshots__');

function readMock(mock: {filepath: string}) {
  const {data} = JSON.parse(fs.readFileSync(mock.filepath).toString());
  return data.pipelineSnapshotOrError as PipelineExplorerRootQuery_pipelineSnapshotOrError_PipelineSnapshot;
}

function svgForPipeline(
  name: string,
  solids: PipelineGraphSolidFragment[],
  parent?: PipelineGraphSolidFragment,
) {
  // render the pipeline explorer's viewport contents to SVG and capture
  // styled-component styles into a <div>
  const layout = getDagrePipelineLayout(solids, parent);
  const div = document.createElement('div');
  const svgContent = ReactDOM.renderToStaticMarkup(
    <StyleSheetManager target={div}>
      <PipelineGraphContents
        minified={false}
        solids={solids}
        parentSolid={parent}
        focusSolids={[]}
        pipelineName={name}
        layout={layout}
        backgroundColor={Colors.LIGHT_GRAY5}
        highlightedSolids={[]}
      />
    </StyleSheetManager>,
  );

  return pretty(
    `<svg
      version="1.1"
      xmlns="http://www.w3.org/2000/svg"
      viewbox="0 0 ${layout.width} ${layout.height}"
      width="${layout.width}"
      height="${layout.height}"
    >
      ${div.innerHTML}
      ${svgContent}
    </svg>`,
  );
}

MOCKS.forEach((mock) => {
  it(`${mock.name}: renders the expected SVG`, () => {
    // load the GraphQL response and pull out the first layer of solids
    const solids = readMock(mock).solidHandles.map((h) => h.solid);

    const expectedPath = path.join(snapshotsDir, `${mock.name}.svg`);
    const actualPath = path.join(snapshotsDir, `${mock.name}.actual.svg`);
    const actual = svgForPipeline(mock.name, solids);

    // write out the actual result for easy visual comparison and compare to existing
    fs.writeFileSync(actualPath, actual);
    if (fs.existsSync(expectedPath)) {
      expect(fs.readFileSync(expectedPath).toString()).toEqual(actual);
    }
  });
});

it(`renders the expected SVG when viewing a composite`, () => {
  // load the GraphQL response and pull out the first layer of solids
  const pipeline = readMock(
    MOCKS.find((m) => m.name === 'airline_demo_ingest_pipeline_composite')!,
  );
  const solids = pipeline.solidHandles.map((h) => h.solid);

  const expectedPath = path.join(snapshotsDir, `airline-composite.svg`);
  const actualPath = path.join(snapshotsDir, `airline-composite.actual.svg`);
  const actual = svgForPipeline(name, solids, pipeline.solidHandle?.solid);

  // write out the actual result for easy visual comparison and compare to existing
  fs.writeFileSync(actualPath, actual);
  if (fs.existsSync(expectedPath)) {
    expect(fs.readFileSync(expectedPath).toString()).toEqual(actual);
  }
});
