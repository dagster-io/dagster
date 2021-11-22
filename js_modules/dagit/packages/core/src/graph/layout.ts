import * as dagre from 'dagre';

import {titleOfIO} from '../app/titleOfIO';

type ILayoutConnectionMember = {
  point: IPoint;
  opName: string;
  edgeName: string;
};

export type ILayoutConnection = {
  from: ILayoutConnectionMember;
  to: ILayoutConnectionMember;
};

export type IFullPipelineLayout = {
  width: number;
  height: number;
  parent: IParentOpLayout | null;
  connections: Array<ILayoutConnection>;
  ops: {
    [opName: string]: IFullOpLayout;
  };
};

export interface IFullOpLayout {
  op: ILayout;
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

interface IParentOpLayout extends Omit<IFullOpLayout, 'op'> {
  mappingLeftEdge: number;
  mappingLeftSpacing: number;
  dependsOn: {[opName: string]: IPoint};
  dependedBy: {[opName: string]: IPoint};
  invocationBoundingBox: ILayout;
}

export interface ILayoutOp {
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
const OP_WIDTH = 370;
const OP_BASE_HEIGHT = 52;
const IO_HEIGHT = 26;
const IO_INSET = 0;
const IO_MINI_WIDTH = 35;
const IO_THRESHOLD_FOR_MINI = 4;
const PORT_INSET_X = 13;
const PORT_INSET_Y = IO_HEIGHT / 2;
const PARENT_DEFINITION_PADDING = 70;
const PARENT_INVOCATION_PADDING = 70;
const EXTERNAL_DEPENDENCY_PADDING = 50;

const MARGIN_BASE = 100;

type OpLinkInfo = {
  solid: {name: string};
  definition: {name: string};
};

function flattenIO(arrays: OpLinkInfo[][]) {
  const map: {[key: string]: OpLinkInfo} = {};
  arrays.forEach((array) => array.forEach((item) => (map[titleOfIO(item)] = item)));
  return Object.values(map);
}

export function layoutPipeline(
  pipelineOps: ILayoutOp[],
  parentOp?: ILayoutOp,
): IFullPipelineLayout {
  const g = new dagre.graphlib.Graph();

  // First, identify how much space we need to pad the DAG by in order to show the
  // parent op AROUND it. We pass this padding in to dagre, and then we have enough
  // room to add our parent layout around the result.
  let parentIOPadding = 0;
  let marginy = MARGIN_BASE;
  let marginx = MARGIN_BASE;
  if (parentOp) {
    parentIOPadding = Math.max(parentOp.inputs.length, parentOp.outputs.length) * IO_HEIGHT;
    marginx = PARENT_DEFINITION_PADDING + PARENT_INVOCATION_PADDING;
    marginy = marginx + parentIOPadding;
  }

  // Define a new top-down, left to right graph layout
  g.setGraph({rankdir: 'TB', marginx, marginy});
  g.setDefaultEdgeLabel(() => ({}));

  const connections: Array<ILayoutConnection> = [];
  const opNamesPresent: {[name: string]: boolean} = {};

  pipelineOps.forEach((op) => {
    opNamesPresent[op.name] = true;
  });
  pipelineOps.forEach((op) => {
    // Lay out each op individually to get it's width and height based on it's
    // inputs and outputs, and then attach it to the graph. Dagre will give us it's
    // x,y position.
    const layout = layoutOp(op, {x: 0, y: 0});
    g.setNode(op.name, {
      width: layout.boundingBox.width,
      height: layout.boundingBox.height,
    });

    // Give Dagre the dependency edges and build a flat set of them so we
    // can reference them in a single pass later
    op.inputs.forEach((input) => {
      input.dependsOn.forEach((dep) => {
        if (opNamesPresent[dep.solid.name] && opNamesPresent[op.name]) {
          g.setEdge({v: dep.solid.name, w: op.name}, {weight: 1});

          connections.push({
            from: {
              point: {x: 0, y: 0},
              opName: dep.solid.name,
              edgeName: dep.definition.name,
            },
            to: {
              point: {x: 0, y: 0},
              opName: op.name,
              edgeName: input.definition.name,
            },
          });
        }
      });
    });
  });

  dagre.layout(g);

  const ops: {[opName: string]: IFullOpLayout} = {};
  const nodesByOp: {[opName: string]: dagre.Node} = {};
  g.nodes().forEach(function (opName) {
    const node = g.node(opName);
    if (!node) {
      return;
    }
    nodesByOp[opName] = node;
  });

  if (MAX_PER_ROW_ENABLED) {
    const nodesInRows: {[key: string]: dagre.Node[]} = {};
    g.nodes().forEach(function (opName) {
      const node = g.node(opName);
      if (!node) {
        return;
      }
      nodesInRows[`${node.y}`] = nodesInRows[`${node.y}`] || [];
      nodesInRows[`${node.y}`].push(node);
    });

    // OK! We're going to split the nodes in long (>MAX_PER_ROW) rows into
    // multiple rows, shift all the subsequent rows down. Note we do this
    // repeatedly until each row has less than MAX_PER_ROW nodes. There are
    // a few caveats to this:
    // - We may end up making the lines betwee nodes and their children
    //   less direct.
    // - We may "compact" two groups of ops separated by horizontal
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
      if (desiredCount === 1) {
        continue;
      }

      for (let r = 0; r < desiredCount; r++) {
        const newRowNodes = rowNodes.slice(r * MAX_PER_ROW, (r + 1) * MAX_PER_ROW);
        const maxHeight = Math.max(...newRowNodes.map((n) => n.height)) + OP_BASE_HEIGHT;
        const totalWidth = newRowNodes.reduce((sum, n) => sum + n.width + OP_BASE_HEIGHT, 0);

        let x = firstRowCenterX - totalWidth / 2;

        // shift the nodes before the split point so they're centered nicely
        newRowNodes.forEach((n) => {
          n.x = x;
          x += n.width + OP_BASE_HEIGHT;
        });

        // shift the nodes after the split point downwards
        const shifted = rowNodes.slice((r + 1) * MAX_PER_ROW);
        shifted.forEach((n) => (n.y += maxHeight));

        // shift all nodes in the graph beneath this row down by
        // the height of the newly inserted row.
        const shiftedMaxHeight = Math.max(0, ...shifted.map((n) => n.height)) + OP_BASE_HEIGHT;

        for (let jj = ii + 1; jj < rows.length; jj++) {
          nodesInRows[`${rows[jj]}`].forEach((n) => (n.y += shiftedMaxHeight));
        }
      }
    }
    let minX = Number.MAX_SAFE_INTEGER;
    Object.keys(nodesByOp).forEach((opName) => {
      const node = nodesByOp[opName];
      minX = Math.min(minX, node.x - node.width / 2 - marginx);
    });
    Object.keys(nodesByOp).forEach((opName) => {
      const node = nodesByOp[opName];
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
  Object.keys(nodesByOp).forEach((opName) => {
    const node = nodesByOp[opName];
    const op = pipelineOps.find(({name}) => name === opName);
    if (!op) {
      return;
    }

    const x = node.x - node.width / 2; // Dagre's x/y is the center, we want top left
    const y = node.y - node.height / 2;
    ops[opName] = layoutOp(op, {x, y});
    maxWidth = Math.max(maxWidth, x + node.width);
    maxHeight = Math.max(maxHeight, y + node.height);
  });

  // Read the Dagre layout and map "edges" back to our data model. We don't
  // currently use the "closest points on the node" Dagre suggests (but we could).
  g.edges().forEach(function (e) {
    const conn = connections.find((c) => c.from.opName === e.v && c.to.opName === e.w);
    const points = g.edge(e).points;
    if (conn) {
      conn.from.point = points[0];
      conn.to.point = points[points.length - 1];
    }
  });

  const result: IFullPipelineLayout = {
    ops,
    connections,
    width: maxWidth + marginx,
    height: maxHeight + marginy,
    parent: null,
  };
  console.log(result);

  if (parentOp) {
    // Now that we've computed the pipeline layout fully, lay out the
    // composite op around the completed DAG.
    result.parent = layoutParentGraphOp(result, parentOp, parentIOPadding);
  }

  return result;
}

function layoutParentGraphOp(layout: IFullPipelineLayout, op: ILayoutOp, parentIOPadding: number) {
  const result: IParentOpLayout = {
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
      flattenIO(op.inputs.map((d) => d.dependsOn)),
      -EXTERNAL_DEPENDENCY_PADDING,
      layout.width,
    ),
    dependedBy: layoutExternalConnections(
      flattenIO(op.outputs.map((d) => d.dependedBy)),
      layout.height + EXTERNAL_DEPENDENCY_PADDING,
      layout.width,
    ),
  };

  const boundingBottom = result.boundingBox.y + result.boundingBox.height;

  op.inputs.forEach((input, idx) => {
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

  op.outputs.forEach((output, idx) => {
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

function layoutExternalConnections(links: OpLinkInfo[], y: number, layoutWidth: number) {
  // fill evenly from 0 to layoutWidth from left to right, then center them if there's overflow.
  const inset = PARENT_INVOCATION_PADDING + PORT_INSET_X;
  const insetWidth = layoutWidth - inset * 2;
  const spacing = Math.max(200, insetWidth / links.length);
  const baseX = inset + Math.min(0, (insetWidth - links.length * spacing) / 2);
  const yShift = spacing < 300 ? 20 : 0;

  const result: {[opName: string]: IPoint} = {};
  links.forEach((link, idx) => {
    const shiftDirection = 1 - (idx % 2) * 2; // 1 or -1, alternating
    result[titleOfIO(link)] = {
      x: baseX + idx * spacing,
      y: y + yShift * shiftDirection,
    };
  });
  return result;
}

export function layoutOp(op: ILayoutOp, root: IPoint): IFullOpLayout {
  // Starting at the root (top left) X,Y, return the layout information for a solid with
  // input blocks, then the main block, then output blocks (arranged vertically)
  let accY = root.y;

  const inputsLayouts: {
    [inputName: string]: {layout: ILayout; port: IPoint};
  } = {};

  const buildIOSmallLayout = (idx: number, count: number) => {
    const centeringOffsetX = (OP_WIDTH - IO_MINI_WIDTH * count) / 2;
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

  op.inputs.forEach((input, idx) => {
    inputsLayouts[input.definition.name] =
      op.inputs.length > IO_THRESHOLD_FOR_MINI
        ? buildIOSmallLayout(idx, op.inputs.length)
        : buildIOLayout();
  });
  if (op.inputs.length > IO_THRESHOLD_FOR_MINI) {
    accY += IO_HEIGHT;
  }

  const opLayout: ILayout = {
    x: root.x,
    y: Math.max(root.y, accY - IO_INSET),
    width: OP_WIDTH,
    height: OP_BASE_HEIGHT + IO_INSET * 2,
  };

  accY += OP_BASE_HEIGHT;

  const outputLayouts: {
    [outputName: string]: {
      layout: ILayout;
      port: IPoint;
    };
  } = {};

  op.outputs.forEach((output, idx) => {
    outputLayouts[output.definition.name] =
      op.outputs.length > IO_THRESHOLD_FOR_MINI
        ? buildIOSmallLayout(idx, op.outputs.length)
        : buildIOLayout();
  });
  if (op.outputs.length > IO_THRESHOLD_FOR_MINI) {
    accY += IO_HEIGHT;
  }

  return {
    boundingBox: {
      x: root.x - 5,
      y: root.y - 5,
      width: OP_WIDTH + 10,
      height: accY - root.y + 10,
    },
    op: opLayout,
    inputs: inputsLayouts,
    outputs: outputLayouts,
  };
}
