import * as dagre from "dagre";

export type IFullPipelineLayout = {
  solids: {
    [solidName: string]: IFullSolidLayout;
  };
  width: number;
  height: number;
};

export interface IFullSolidLayout {
  solid: ILayout;
  inputs: {
    [inputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  };
  outputs: {
    [outputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  };
}

export interface ILayoutPipeline {
  solids: Array<ILayoutSolid>;
}

interface ILayoutSolid {
  name: string;
  inputs: Array<{
    name: string;
    dependsOn: {
      name: string;
      solid: {
        name: string;
      };
    } | null;
  }>;
  outputs: Array<{
    name: string;
  }>;
}

export interface ILayout {
  x: number;
  y: number;
  height: number;
  width: number;
}

export interface IPoint {
  x: number;
  y: number;
}

const SOLID_WIDTH = 250;
const SOLID_BASE_HEIGHT = 60;
const SOLID_GAP = 100;
const INPUT_WIDTH = 200;
const INPUT_HEIGHT = 80;
const INPUT_GAP = 20;
const OUTPUT_WIDTH = 200;
const OUTPUT_HEIGHT = 80;
const INPUT_OUTPUT_INSET = 10;

export function getDagrePipelineLayout(
  pipeline: ILayoutPipeline
): IFullPipelineLayout {
  const g = new dagre.graphlib.Graph();
  g.setGraph({
    rankdir: "LR",
    align: "UL",
    marginx: 100,
    marginy: 100
  });
  g.setDefaultEdgeLabel(function() {
    return {};
  });

  pipeline.solids.forEach(solid => {
    const layout = layoutSolid({ solid, x: 0, y: 0 });
    g.setNode(solid.name, {
      height: layout.solid.height,
      width: layout.solid.width + INPUT_WIDTH * 2 - INPUT_OUTPUT_INSET * 2
    });

    solid.inputs.forEach(input => {
      if (input.dependsOn) {
        g.setEdge(input.dependsOn.solid.name, solid.name);
      }
    });
  });

  dagre.layout(g);

  const solids: {
    [solidName: string]: IFullSolidLayout;
  } = {};
  g.nodes().forEach(function(solidName) {
    const node = g.node(solidName);
    const solid = pipeline.solids.find(({ name }) => name === solidName);
    if (solid) {
      solids[solidName] = layoutSolid({
        solid: solid,
        x: node.x,
        y: node.y
      });
    }
  });
  // g.edges().forEach(function(e) {
  //   console.log(
  //     "Edge " + e.v + " -> " + e.w + ": " + JSON.stringify(g.edge(e))
  //   );
  // });

  return {
    solids,
    width: g.graph().width as number,
    height: g.graph().height as number
  };
}

function layoutSolid({
  solid,
  x: solidX,
  y: solidY
}: {
  solid: ILayoutSolid;
  x: number;
  y: number;
}): IFullSolidLayout {
  const solidLayout: ILayout = {
    x: solidX,
    y: solidY,
    width: SOLID_WIDTH,
    height:
      SOLID_BASE_HEIGHT +
      (INPUT_HEIGHT + INPUT_GAP) *
        Math.max(solid.inputs.length, solid.outputs.length)
  };
  const inputs: {
    [inputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  } = {};
  solid.inputs.forEach((input, i) => {
    const inputX = solidX + INPUT_OUTPUT_INSET - INPUT_WIDTH;
    const inputY = solidY + INPUT_GAP + (INPUT_HEIGHT + INPUT_GAP) * i;
    inputs[input.name] = {
      layout: {
        x: inputX,
        y: inputY,
        width: INPUT_WIDTH,
        height: INPUT_HEIGHT
      },
      port: {
        x: inputX,
        y: inputY + INPUT_HEIGHT / 2
      }
    };
  });

  const outputs: {
    [outputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  } = {};
  solid.outputs.forEach((output, i) => {
    const outputX = solidX + SOLID_WIDTH - INPUT_OUTPUT_INSET;
    const outputY = solidY + INPUT_GAP + (OUTPUT_HEIGHT + INPUT_GAP) * i;
    outputs[output.name] = {
      layout: {
        x: outputX,
        y: outputY,
        width: OUTPUT_WIDTH,
        height: OUTPUT_HEIGHT
      },
      port: {
        x: outputX,
        y: outputY + OUTPUT_HEIGHT / 2
      }
    };
  });

  return {
    solid: solidLayout,
    inputs,
    outputs
  };
}
