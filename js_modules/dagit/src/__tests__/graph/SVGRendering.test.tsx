import * as React from "react";
import * as ReactDOM from "react-dom/server";
import { StyleSheetManager } from "styled-components";
import { Colors } from "@blueprintjs/core";
import { print } from "graphql/language/printer";
import pretty from "pretty";
import fs from "fs";

import { PipelineGraphContents } from "../../graph/PipelineGraph";
import { getDagrePipelineLayout } from "../../graph/getFullSolidLayout";
import { PipelineExplorerRootQuery_pipelineOrError_Pipeline } from "../../types/PipelineExplorerRootQuery";
import { PIPELINE_EXPLORER_ROOT_QUERY } from "../../PipelineExplorerRoot";
import { PipelineGraphSolidFragment } from "../../graph/types/PipelineGraphSolidFragment";

const PipelineNames = [
  "airline_demo_ingest_pipeline",
  "airline_demo_warehouse_pipeline",
  "composition",
  "log_spew",
  "many_events",
  "fan_in_fan_out_pipeline"
];

// Write out a file that can be used to re-create the mock data
fs.writeFileSync(
  `${__dirname}/data/refetch.sh`,
  `#!/bin/bash\n\n` +
    PipelineNames.map(
      name =>
        `curl -X POST -H "Content-Type: application/json" --data '${JSON.stringify(
          {
            variables: { name },
            query: print(PIPELINE_EXPLORER_ROOT_QUERY)
              .replace(/[\n\r]/g, "")
              .replace(/[ ][ ]+/g, " ")
          }
        )}' http://localhost:3333/graphql > ${name}.json`
    ).join("\n\n")
);

function pipelineNamed(name: string) {
  const result = JSON.parse(
    fs.readFileSync(`${__dirname}/data/${name}.json`).toString()
  );
  return result.data
    .pipelineOrError as PipelineExplorerRootQuery_pipelineOrError_Pipeline;
}

function svgForPipeline(
  name: string,
  solids: PipelineGraphSolidFragment[],
  parent?: PipelineGraphSolidFragment
) {
  // render the pipeline explorer's viewport contents to SVG and capture
  // styled-component styles into a <div>
  const layout = getDagrePipelineLayout(solids, parent);
  const div = document.createElement("div");
  const svgContent = ReactDOM.renderToStaticMarkup(
    <StyleSheetManager target={div}>
      <PipelineGraphContents
        minified={false}
        solids={solids}
        parentSolid={parent}
        pipelineName={name}
        layout={layout}
        backgroundColor={Colors.LIGHT_GRAY5}
        highlightedSolids={[]}
      />
    </StyleSheetManager>
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
    </svg>`
  );
}

PipelineNames.forEach(name => {
  it(`${name}: renders the expected SVG`, () => {
    // load the GraphQL response and pull out the first layer of solids
    const solids = pipelineNamed(name)
      .solidHandles.filter(h => !h.parent)
      .map(h => h.solid);

    const expectedPath = `${__dirname}/svg-snapshots/${name}.svg`;
    const actualPath = `${__dirname}/svg-snapshots/${name}.actual.svg`;
    const actual = svgForPipeline(name, solids);

    // write out the actual result for easy visual comparison and compare to existing
    fs.writeFileSync(actualPath, actual);
    if (fs.existsSync(expectedPath)) {
      expect(fs.readFileSync(expectedPath).toString()).toEqual(actual);
    }
  });
});

it(`renders the expected SVG when viewing a composite`, () => {
  // load the GraphQL response and pull out the first layer of solids
  const pipeline = pipelineNamed("airline_demo_ingest_pipeline");
  const parentId = "master_cord_s3_to_df";
  const parent = pipeline.solidHandles.find(h => h.handleID === parentId)!
    .solid;

  const solids = pipeline.solidHandles
    .filter(h => h.parent && h.parent.handleID === parentId)
    .map(h => h.solid);

  const expectedPath = `${__dirname}/svg-snapshots/airline-composite.svg`;
  const actualPath = `${__dirname}/svg-snapshots/airline-composite.actual.svg`;
  const actual = svgForPipeline(name, solids, parent);

  // write out the actual result for easy visual comparison and compare to existing
  fs.writeFileSync(actualPath, actual);
  if (fs.existsSync(expectedPath)) {
    expect(fs.readFileSync(expectedPath).toString()).toEqual(actual);
  }
});
