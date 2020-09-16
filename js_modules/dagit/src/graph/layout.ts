import * as dagre from 'dagre';

import {titleOfIO} from '../Util';

export type IPipelineLayoutParams = {
  solids: ILayoutSolid[];
  parentSolid: ILayoutSolid | undefined;
};

export type ILayoutConnectionMember = {
  point: IPoint;
  solidName: string;
  edgeName: string;
};

export type ILayoutConnection = {
  from: ILayoutConnectionMember;
  to: ILayoutConnectionMember;
};

export type IFullPipelineLayout = {
  width: number;
  height: number;
  parent: IParentSolidLayout | null;
  connections: Array<ILayoutConnection>;
  solids: {
    [solidName: string]: IFullSolidLayout;
  };
};

export interface IFullSolidLayout {
  solid: ILayout;
  boundingBox: ILayout;
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

interface IParentSolidLayout extends Omit<IFullSolidLayout, 'solid'> {
  mappingLeftEdge: number;
  mappingLeftSpacing: number;
  dependsOn: {[solidName: string]: IPoint};
  dependedBy: {[solidName: string]: IPoint};
  invocationBoundingBox: ILayout;
}

export interface ILayoutSolid {
  name: string;
  inputs: Array<{
    definition: {
      name: string;
    };
    dependsOn: Array<{
      definition: {
        name: string;
      };
      solid: {
        name: string;
      };
    }>;
  }>;
  outputs: Array<{
    definition: {
      name: string;
    };
    dependedBy: Array<{
      definition: {
        name: string;
      };
      solid: {
        name: string;
      };
    }>;
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

const MAX_PER_ROW_ENABLED = false;
const MAX_PER_ROW = 25;
const SOLID_WIDTH = 370;
const SOLID_BASE_HEIGHT = 75;
const IO_HEIGHT = 36;
const IO_INSET = 6;
const IO_MINI_WIDTH = 35;
const IO_THRESHOLD_FOR_MINI = 4;
const PORT_INSET_X = 15;
const PORT_INSET_Y = IO_HEIGHT / 2;
const PARENT_DEFINITION_PADDING = 70;
const PARENT_INVOCATION_PADDING = 70;
const EXTERNAL_DEPENDENCY_PADDING = 50;

type SolidLinkInfo = {
  solid: {name: string};
  definition: {name: string};
};

function flattenIO(arrays: SolidLinkInfo[][]) {
  const map: {[key: string]: SolidLinkInfo} = {};
  arrays.forEach((array) => array.forEach((item) => (map[titleOfIO(item)] = item)));
  return Object.values(map);
}

export function layoutPipeline(
  pipelineSolids: ILayoutSolid[],
  parentSolid?: ILayoutSolid,
): IFullPipelineLayout {
  const g = new dagre.graphlib.Graph();

  // First, identify how much space we need to pad the DAG by in order to show the
  // parent solid AROUND it. We pass this padding in to dagre, and then we have enough
  // room to add our parent layout around the result.
  let parentIOPadding = 0;
  const marginBase = 100;
  let marginy = marginBase;
  let marginx = marginBase;
  if (parentSolid) {
    parentIOPadding = Math.max(parentSolid.inputs.length, parentSolid.outputs.length) * IO_HEIGHT;
    marginx = PARENT_DEFINITION_PADDING + PARENT_INVOCATION_PADDING;
    marginy = marginx + parentIOPadding;
  }

  // Define a new top-down, left to right graph layout
  g.setGraph({rankdir: 'TB', marginx, marginy});
  g.setDefaultEdgeLabel(() => ({}));

  const connections: Array<ILayoutConnection> = [];
  const solidNamesPresent: {[name: string]: boolean} = {};

  pipelineSolids.forEach((solid) => {
    solidNamesPresent[solid.name] = true;
  });
  pipelineSolids.forEach((solid) => {
    // Lay out each solid individually to get it's width and height based on it's
    // inputs and outputs, and then attach it to the graph. Dagre will give us it's
    // x,y position.
    const layout = layoutSolid(solid, {x: 0, y: 0});
    g.setNode(solid.name, {
      width: layout.boundingBox.width,
      height: layout.boundingBox.height,
    });

    // Give Dagre the dependency edges and build a flat set of them so we
    // can reference them in a single pass later
    solid.inputs.forEach((input) => {
      input.dependsOn.forEach((dep) => {
        if (solidNamesPresent[dep.solid.name] && solidNamesPresent[solid.name]) {
          g.setEdge({v: dep.solid.name, w: solid.name}, {weight: 1});

          connections.push({
            from: {
              point: {x: 0, y: 0},
              solidName: dep.solid.name,
              edgeName: dep.definition.name,
            },
            to: {
              point: {x: 0, y: 0},
              solidName: solid.name,
              edgeName: input.definition.name,
            },
          });
        }
      });
    });
  });

  dagre.layout(g);

  const solids: {[solidName: string]: IFullSolidLayout} = {};
  const nodesBySolid: {[solidName: string]: dagre.Node} = {};
  g.nodes().forEach(function (solidName) {
    const node = g.node(solidName);
    if (!node) return;
    nodesBySolid[solidName] = node;
  });

  if (MAX_PER_ROW_ENABLED) {
    const nodesInRows: {[key: string]: dagre.Node[]} = {};
    g.nodes().forEach(function (solidName) {
      const node = g.node(solidName);
      if (!node) return;
      nodesInRows[`${node.y}`] = nodesInRows[`${node.y}`] || [];
      nodesInRows[`${node.y}`].push(node);
    });

    // OK! We're going to split the nodes in long (>MAX_PER_ROW) rows into
    // multiple rows, shift all the subsequent rows down. Note we do this
    // repeatedly until each row has less than MAX_PER_ROW nodes. There are
    // a few caveats to this:
    // - We may end up making the lines betwee nodes and their children
    //   less direct.
    // - We may "compact" two groups of solids separated by horizontal
    //   whitespace on the same row into the same block.

    const rows = Object.keys(nodesInRows)
      .map((a) => Number(a))
      .sort((a, b) => a - b);

    const firstRow = nodesInRows[`${rows[0]}`];
    const firstRowCenterX = firstRow
      ? firstRow.reduce((s, n) => s + n.x + n.width / 2, 0) / firstRow.length
      : 0;

    for (let ii = 0; ii < rows.length; ii++) {
      const rowKey = `${rows[ii]}`;
      const rowNodes = nodesInRows[rowKey];

      const desiredCount = Math.ceil(rowNodes.length / MAX_PER_ROW);
      if (desiredCount === 1) continue;

      for (let r = 0; r < desiredCount; r++) {
        const newRowNodes = rowNodes.slice(r * MAX_PER_ROW, (r + 1) * MAX_PER_ROW);
        const maxHeight = Math.max(...newRowNodes.map((n) => n.height)) + SOLID_BASE_HEIGHT;
        const totalWidth = newRowNodes.reduce((sum, n) => sum + n.width + SOLID_BASE_HEIGHT, 0);

        let x = firstRowCenterX - totalWidth / 2;

        // shift the nodes before the split point so they're centered nicely
        newRowNodes.forEach((n) => {
          n.x = x;
          x += n.width + SOLID_BASE_HEIGHT;
        });

        // shift the nodes after the split point downwards
        const shifted = rowNodes.slice((r + 1) * MAX_PER_ROW);
        shifted.forEach((n) => (n.y += maxHeight));

        // shift all nodes in the graph beneath this row down by
        // the height of the newly inserted row.
        const shiftedMaxHeight = Math.max(0, ...shifted.map((n) => n.height)) + SOLID_BASE_HEIGHT;

        for (let jj = ii + 1; jj < rows.length; jj++) {
          nodesInRows[`${rows[jj]}`].forEach((n) => (n.y += shiftedMaxHeight));
        }
      }
    }
    let minX = Number.MAX_SAFE_INTEGER;
    Object.keys(nodesBySolid).forEach((solidName) => {
      const node = nodesBySolid[solidName];
      minX = Math.min(minX, node.x - node.width / 2 - marginx);
    });
    Object.keys(nodesBySolid).forEach((solidName) => {
      const node = nodesBySolid[solidName];
      node.x -= minX;
    });
  }

  // Due to a bug in Dagre when run without an "align" value, we need to calculate
  // the total width of the graph coordinate space ourselves. We need the height
  // because we've shifted long single rows into multiple rows.
  let maxWidth = 0;
  let maxHeight = 0;

  // Read the Dagre layout and map "nodes" back to our solids, but with
  // X,Y coordinates this time.
  Object.keys(nodesBySolid).forEach((solidName) => {
    const node = nodesBySolid[solidName];
    const solid = pipelineSolids.find(({name}) => name === solidName);
    if (!solid) return;

    solids[solidName] = layoutSolid(solid, {
      x: node.x - node.width / 2, // Dagre's x/y is the center, we want top left
      y: node.y - node.height / 2,
    });
    maxWidth = Math.max(maxWidth, node.x + node.width);
    maxHeight = Math.max(maxHeight, node.y + node.height);
  });

  // Read the Dagre layout and map "edges" back to our data model. We don't
  // currently use the "closest points on the node" Dagre suggests (but we could).
  g.edges().forEach(function (e) {
    const conn = connections.find((c) => c.from.solidName === e.v && c.to.solidName === e.w);
    const points = g.edge(e).points;
    if (conn) {
      conn.from.point = points[0];
      conn.to.point = points[points.length - 1];
    }
  });

  const result: IFullPipelineLayout = {
    solids,
    connections,
    width: maxWidth,
    height: maxHeight + marginBase,
    parent: null,
  };

  if (parentSolid) {
    // Now that we've computed the pipeline layout fully, lay out the
    // composite solid around the completed DAG.
    result.parent = layoutParentCompositeSolid(result, parentSolid, parentIOPadding);
  }

  return result;
}

function layoutParentCompositeSolid(
  layout: IFullPipelineLayout,
  solid: ILayoutSolid,
  parentIOPadding: number,
) {
  const result: IParentSolidLayout = {
    invocationBoundingBox: {
      x: 1,
      y: 1,
      width: layout.width - 1,
      height: layout.height - 1,
    },
    boundingBox: {
      x: PARENT_INVOCATION_PADDING,
      y: PARENT_INVOCATION_PADDING + parentIOPadding,
      width: layout.width - PARENT_INVOCATION_PADDING * 2,
      height: layout.height - (PARENT_INVOCATION_PADDING + parentIOPadding) * 2,
    },
    mappingLeftEdge: PARENT_INVOCATION_PADDING - 20,
    mappingLeftSpacing: 10,
    inputs: {},
    outputs: {},
    dependsOn: layoutExternalConnections(
      flattenIO(solid.inputs.map((d) => d.dependsOn)),
      -EXTERNAL_DEPENDENCY_PADDING,
      layout.width,
    ),
    dependedBy: layoutExternalConnections(
      flattenIO(solid.outputs.map((d) => d.dependedBy)),
      layout.height + EXTERNAL_DEPENDENCY_PADDING,
      layout.width,
    ),
  };

  const boundingBottom = result.boundingBox.y + result.boundingBox.height;

  solid.inputs.forEach((input, idx) => {
    result.inputs[input.definition.name] = {
      layout: {
        x: result.boundingBox.x,
        y: result.boundingBox.y - idx * IO_HEIGHT - IO_HEIGHT,
        width: 0,
        height: IO_HEIGHT,
      },
      port: {
        x: result.boundingBox.x + PORT_INSET_X,
        y: result.boundingBox.y - idx * IO_HEIGHT - IO_HEIGHT / 2,
      },
    };
  });

  solid.outputs.forEach((output, idx) => {
    result.outputs[output.definition.name] = {
      layout: {
        x: result.boundingBox.x,
        y: boundingBottom + idx * IO_HEIGHT,
        width: 0,
        height: IO_HEIGHT,
      },
      port: {
        x: result.boundingBox.x + PORT_INSET_X,
        y: boundingBottom + idx * IO_HEIGHT + IO_HEIGHT / 2,
      },
    };
  });

  return result;
}

function layoutExternalConnections(links: SolidLinkInfo[], y: number, layoutWidth: number) {
  // fill evenly from 0 to layoutWidth from left to right, then center them if there's overflow.
  const inset = PARENT_INVOCATION_PADDING + PORT_INSET_X;
  const insetWidth = layoutWidth - inset * 2;
  const spacing = Math.max(200, insetWidth / links.length);
  const baseX = inset + Math.min(0, (insetWidth - links.length * spacing) / 2);
  const yShift = spacing < 300 ? 20 : 0;

  const result: {[solidName: string]: IPoint} = {};
  links.forEach((link, idx) => {
    const shiftDirection = 1 - (idx % 2) * 2; // 1 or -1, alternating
    result[titleOfIO(link)] = {
      x: baseX + idx * spacing,
      y: y + yShift * shiftDirection,
    };
  });
  return result;
}

export function layoutSolid(solid: ILayoutSolid, root: IPoint): IFullSolidLayout {
  // Starting at the root (top left) X,Y, return the layout information for a solid with
  // input blocks, then the main block, then output blocks (arranged vertically)
  let accY = root.y;

  const inputsLayouts: {
    [inputName: string]: {layout: ILayout; port: IPoint};
  } = {};

  const buildIOSmallLayout = (idx: number, count: number) => {
    const centeringOffsetX = (SOLID_WIDTH - IO_MINI_WIDTH * count) / 2;
    const x = root.x + IO_MINI_WIDTH * idx + centeringOffsetX;
    return {
      port: {
        x: x + PORT_INSET_X,
        y: accY + PORT_INSET_Y,
      },
      layout: {
        x: x,
        y: accY,
        width: IO_MINI_WIDTH,
        height: IO_HEIGHT,
      },
    };
  };

  const buildIOLayout = () => {
    const layout: {layout: ILayout; port: IPoint} = {
      port: {x: root.x + PORT_INSET_X, y: accY + PORT_INSET_Y},
      layout: {
        x: root.x,
        y: accY,
        width: 0,
        height: IO_HEIGHT,
      },
    };
    accY += IO_HEIGHT;
    return layout;
  };

  solid.inputs.forEach((input, idx) => {
    inputsLayouts[input.definition.name] =
      solid.inputs.length > IO_THRESHOLD_FOR_MINI
        ? buildIOSmallLayout(idx, solid.inputs.length)
        : buildIOLayout();
  });
  if (solid.inputs.length > IO_THRESHOLD_FOR_MINI) {
    accY += IO_HEIGHT;
  }

  const solidLayout: ILayout = {
    x: root.x,
    y: Math.max(root.y, accY - IO_INSET),
    width: SOLID_WIDTH,
    height: SOLID_BASE_HEIGHT + IO_INSET * 2,
  };

  accY += SOLID_BASE_HEIGHT;

  const outputLayouts: {
    [outputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  } = {};

  solid.outputs.forEach((output, idx) => {
    outputLayouts[output.definition.name] =
      solid.outputs.length > IO_THRESHOLD_FOR_MINI
        ? buildIOSmallLayout(idx, solid.outputs.length)
        : buildIOLayout();
  });
  if (solid.outputs.length > IO_THRESHOLD_FOR_MINI) {
    accY += IO_HEIGHT;
  }

  return {
    boundingBox: {
      x: root.x,
      y: root.y,
      width: SOLID_WIDTH,
      height: accY - root.y,
    },
    solid: solidLayout,
    inputs: inputsLayouts,
    outputs: outputLayouts,
  };
}

export function pointsToBox(a: IPoint, b: IPoint): ILayout {
  return {
    x: Math.min(a.x, b.x),
    y: Math.min(a.y, b.y),
    width: Math.abs(a.x - b.x),
    height: Math.abs(a.y - b.y),
  };
}

export function layoutsIntersect(a: ILayout, b: ILayout) {
  return (
    a.x + a.width >= b.x && b.x + b.width >= a.x && a.y + a.height >= b.y && b.y + b.height >= a.y
  );
}
