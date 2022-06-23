import * as dagre from 'dagre';

import {titleOfIO} from '../app/titleOfIO';

import {IBounds, IPoint} from './common';

type OpLayoutEdgeSide = {
  point: IPoint;
  opName: string;
  edgeName: string;
};

export type OpLayoutEdge = {
  from: OpLayoutEdgeSide;
  to: OpLayoutEdgeSide;
};

export interface OpLayout {
  // Overall frame of the box relative to 0,0 on the graph
  bounds: IBounds;

  // Frames of specific components - These need to be computed during layout
  // (rather than at render time) to position edges into inputs/outputs.
  op: IBounds;
  inputs: {
    [inputName: string]: {
      layout: IBounds;
      port: IPoint;
    };
  };
  outputs: {
    [outputName: string]: {
      layout: IBounds;
      port: IPoint;
    };
  };
}

export type OpGraphLayout = {
  width: number;
  height: number;
  parent: ParentOpLayout | null;
  edges: OpLayoutEdge[];
  nodes: {[opName: string]: OpLayout};
};

interface ParentOpLayout extends Omit<OpLayout, 'op'> {
  mappingLeftEdge: number;
  mappingLeftSpacing: number;
  dependsOn: {[opName: string]: IPoint};
  dependedBy: {[opName: string]: IPoint};
  invocationBoundingBox: IBounds;
}

export interface ILayoutOp {
  name: string;
  inputs: {
    definition: {
      name: string;
    };
    dependsOn: {
      definition: {
        name: string;
      };
      solid: {
        name: string;
      };
    }[];
  }[];
  definition: {
    description: string | null;
    assetNodes: {
      assetKey: {
        path: string[];
      };
    }[];
  };
  outputs: {
    definition: {
      name: string;
    };
    dependedBy: {
      definition: {
        name: string;
      };
      solid: {
        name: string;
      };
    }[];
  }[];
}

const OP_WIDTH = 370;
const OP_BASE_HEIGHT = 52;
const OP_ASSETS_ROW_HEIGHT = 22;
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

export function layoutOpGraph(pipelineOps: ILayoutOp[], parentOp?: ILayoutOp): OpGraphLayout {
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

  const edges: OpLayoutEdge[] = [];
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
      width: layout.bounds.width,
      height: layout.bounds.height,
    });

    // Give Dagre the dependency edges and build a flat set of them so we
    // can reference them in a single pass later
    op.inputs.forEach((input) => {
      input.dependsOn.forEach((dep) => {
        if (opNamesPresent[dep.solid.name] && opNamesPresent[op.name]) {
          g.setEdge({v: dep.solid.name, w: op.name}, {weight: 1});

          edges.push({
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

  const ops: {[opName: string]: OpLayout} = {};
  const dagreNodes: {[opName: string]: dagre.Node} = {};
  g.nodes().forEach(function (opName) {
    const node = g.node(opName);
    if (!node) {
      return;
    }
    dagreNodes[opName] = node;
  });

  // Due to a bug in Dagre when run without an "align" value, we need to calculate
  // the total width of the graph coordinate space ourselves. We need the height
  // because we've shifted long single rows into multiple rows.
  let maxWidth = 0;
  let maxHeight = 0;

  // Read the Dagre layout and map "nodes" back to our solids, but with
  // X,Y coordinates this time.
  Object.keys(dagreNodes).forEach((opName) => {
    const node = dagreNodes[opName];
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
    const conn = edges.find((c) => c.from.opName === e.v && c.to.opName === e.w);
    const points = g.edge(e).points;
    if (conn) {
      conn.from.point = points[0];
      conn.to.point = points[points.length - 1];
    }
  });

  const result: OpGraphLayout = {
    edges,
    nodes: ops,
    width: maxWidth + marginx,
    height: maxHeight + marginy,
    parent: null,
  };

  if (parentOp) {
    // Now that we've computed the pipeline layout fully, lay out the
    // composite op around the completed DAG.
    result.parent = layoutParentGraphOp(result, parentOp, parentIOPadding);
  }

  return result;
}

function layoutParentGraphOp(layout: OpGraphLayout, op: ILayoutOp, parentIOPadding: number) {
  const result: ParentOpLayout = {
    invocationBoundingBox: {
      x: 1,
      y: 1,
      width: layout.width - 1,
      height: layout.height - 1,
    },
    bounds: {
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

  const boundingBottom = result.bounds.y + result.bounds.height;

  op.inputs.forEach((input, idx) => {
    result.inputs[input.definition.name] = {
      layout: {
        x: result.bounds.x,
        y: result.bounds.y - idx * IO_HEIGHT - IO_HEIGHT,
        width: 0,
        height: IO_HEIGHT,
      },
      port: {
        x: result.bounds.x + PORT_INSET_X,
        y: result.bounds.y - idx * IO_HEIGHT - IO_HEIGHT / 2,
      },
    };
  });

  op.outputs.forEach((output, idx) => {
    result.outputs[output.definition.name] = {
      layout: {
        x: result.bounds.x,
        y: boundingBottom + idx * IO_HEIGHT,
        width: 0,
        height: IO_HEIGHT,
      },
      port: {
        x: result.bounds.x + PORT_INSET_X,
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

export function layoutOp(op: ILayoutOp, root: IPoint): OpLayout {
  // Starting at the root (top left) X,Y, return the layout information for a solid with
  // input blocks, then the main block, then output blocks (arranged vertically)
  let accY = root.y;

  const inputsLayouts: {
    [inputName: string]: {layout: IBounds; port: IPoint};
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
        x,
        y: accY,
        width: IO_MINI_WIDTH,
        height: IO_HEIGHT,
      },
    };
  };

  const buildIOLayout = () => {
    const layout: {layout: IBounds; port: IPoint} = {
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

  const opLayout: IBounds = {
    x: root.x,
    y: Math.max(root.y, accY - IO_INSET),
    width: OP_WIDTH,
    height: OP_BASE_HEIGHT + IO_INSET * 2,
  };

  accY += OP_BASE_HEIGHT;

  if (op.definition.assetNodes.length && op.definition.description) {
    opLayout.height += OP_ASSETS_ROW_HEIGHT;
    accY += OP_ASSETS_ROW_HEIGHT;
  }

  const outputLayouts: {
    [outputName: string]: {
      layout: IBounds;
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
    bounds: {
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
