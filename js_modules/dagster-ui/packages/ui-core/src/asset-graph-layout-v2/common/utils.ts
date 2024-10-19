import {AssetNode, GroupNode, ModelGraph, ModelNode, NodeType} from './ModelGraph';
import {CATMULLROM_CURVE_TENSION, WEBGL_CURVE_SEGMENTS} from './conts';
import {Point} from '../common/types';

const CANVAS = new OffscreenCanvas(300, 300);

/** Checks whether the given node is an op node. */
export function isAssetNode(node: ModelNode | undefined): node is AssetNode {
  return node?.nodeType === NodeType.ASSET_NODE;
}

/** Checks whether the given node is a group node. */
export function isGroupNode(node: ModelNode | undefined): node is GroupNode {
  return node?.nodeType === NodeType.GROUP_NODE;
}

/** Generates unique id. */
export function genUid(): string {
  return Math.random().toString(36).slice(-6);
}

/** Gets the deepest expanded group node ids. */
export function getDeepestExpandedGroupNodeIds(
  root: GroupNode | undefined,
  modelGraph: ModelGraph,
  deepestExpandedGroupNodeIds: string[],
  ignoreExpandedState = false,
) {
  let childrenIds: string[] = [];
  if (root == null) {
    childrenIds = modelGraph.rootNodes.map((node) => node.id);
  } else {
    childrenIds = root.childrenIds || [];
  }
  for (const childNodeId of childrenIds) {
    const childNode = modelGraph.nodesById[childNodeId];
    if (!childNode) {
      continue;
    }
    if (
      isGroupNode(childNode) &&
      (ignoreExpandedState || (!ignoreExpandedState && childNode.expanded))
    ) {
      const childrenIds = childNode.childrenIds || [];
      const isDeepest = ignoreExpandedState
        ? childrenIds.filter((id) => isGroupNode(modelGraph.nodesById[id])).length === 0
        : childrenIds
            .filter((id) => isGroupNode(modelGraph.nodesById[id]))
            .every((id) => !(modelGraph.nodesById[id] as GroupNode).expanded);
      if (isDeepest) {
        deepestExpandedGroupNodeIds.push(childNode.id);
      }
      getDeepestExpandedGroupNodeIds(
        childNode,
        modelGraph,
        deepestExpandedGroupNodeIds,
        ignoreExpandedState,
      );
    }
  }
}

/** Gets the points from a smooth curve that go through the given points. */
export function generateCurvePoints(
  points: Point[],
  d3Line: any,
  d3CurveMonotoneY: any,
  three: any,
): Point[] {
  let curvePoints: Point[] = [];
  if (points.length === 2) {
    curvePoints = points;
  } else if (
    points.length === 3 &&
    points[0]!.x === points[1]!.x &&
    points[1]!.x === points[2]!.x
  ) {
    curvePoints = points;
  } else {
    // Check if points are sorted by their Y coordinate.
    let isYSorted = true;
    let curOrder = 0;
    for (let i = 0; i < points.length - 1; i++) {
      const curPt = points[i]!;
      const nextPt = points[i + 1]!;
      const order = nextPt > curPt ? 1 : -1;
      if (curOrder !== 0 && curOrder !== order) {
        isYSorted = false;
        break;
      }
      curOrder = order;
    }

    // If ys are sorted, use d3's curveMonotoneY to generate curves and
    // convert them to a CurvePath in threejs. curveMonotoneY looks better
    // then catmullrom curves.
    const vec3 = three['Vector3'];
    if (isYSorted) {
      const d3Curve = d3Line()
        .x((d: Point) => d.x)
        .y((d: Point) => d.y)
        .curve(d3CurveMonotoneY)(points) as string;
      const parts = d3Curve
        .split(/M|C/)
        .filter((s) => s !== '')
        .map((s) => s.split(',').map((s) => Number(s)));
      let curStartPoint = new vec3(parts[0]![0], parts[0]![1], 0);
      const curvePath = new three['CurvePath']();
      for (let i = 1; i < parts.length; i++) {
        const curPart = parts[i]!;
        if (curPart.length === 6) {
          const ptStart = curStartPoint;
          const c1 = new vec3(curPart[0], curPart[1]);
          const c2 = new vec3(curPart[2], curPart[3]);
          const ptEnd = new vec3(curPart[4], curPart[5]);
          curStartPoint = ptEnd;
          const curve = new three['CubicBezierCurve3'](ptStart, c1, c2, ptEnd);
          curvePath.add(curve);
        }
      }
      curvePoints = curvePath['getPoints'](WEBGL_CURVE_SEGMENTS);
    }
    // Otherwise, use the catmullrom curve.
    else {
      const v3Points = points.map((point) => new vec3(point.x, point.y, 0));
      const curve = new three['CatmullRomCurve3'](
        v3Points,
        false,
        'catmullrom',
        CATMULLROM_CURVE_TENSION,
      );
      curvePoints = curve['getPoints'](WEBGL_CURVE_SEGMENTS);
    }
  }
  return curvePoints;
}

/** Cache for label width indexed by label. */
const LABEL_WIDTHS: {[label: string]: number} = {};

/** Gets the label width by measureing its size in canvas. */
export function getLabelWidth(
  label: string,
  fontSize: number,
  bold: boolean,
  saveToCache = true,
): number {
  // Check cache first.
  const key = `${label}___${fontSize}___${bold}`;
  let labelWidth = LABEL_WIDTHS[key];
  if (labelWidth == null) {
    // On cache miss, render the text to a offscreen canvas to get its width.
    const context = CANVAS.getContext('2d')! as unknown as CanvasRenderingContext2D;
    context.font = `${fontSize}px "Google Sans Text", Arial, Helvetica, sans-serif`;
    if (bold) {
      context.font = `bold ${context.font}`;
    }
    const metrics = context.measureText(label);
    const width = metrics.width;
    if (saveToCache) {
      LABEL_WIDTHS[key] = width;
    }
    labelWidth = width;
  }
  return labelWidth;
}

/**
 * Given two namespace strings, e.g. a/b/c/d and a/b/x, returns the common
 * prefix, e.g. a/b.
 */
export function findCommonNamespace(ns1: string, ns2: string): string {
  const ns1Parts = ns1.split('/');
  const ns2Parts = ns2.split('/');
  let commonPrefix = '';
  for (let i = Math.min(ns1Parts.length, ns2Parts.length); i > 0; i--) {
    const ns1Prefix = ns1Parts.slice(0, i).join('/');
    const ns2Prefix = ns2Parts.slice(0, i).join('/');
    if (ns1Prefix === ns2Prefix) {
      commonPrefix = ns2Prefix;
      break;
    }
  }
  return commonPrefix;
}

/** Gets the next level namespace part right after baseNs up to fullNs. */
export function getNextLevelNsPart(baseNs: string, fullNs: string): string {
  if (baseNs === fullNs) {
    return '';
  }
  const baseNsParts = baseNs.split('/').filter((part) => part !== '');
  const fullNsParts = fullNs.split('/').filter((part) => part !== '');
  if (fullNsParts.length === 0) {
    return '';
  }
  return fullNsParts[baseNsParts.length]!;
}

export function isNodeExpanded(nodeId: string, modelGraph: ModelGraph) {
  const node = modelGraph.nodesById[nodeId];
  if (!node) {
    return false;
  }
  const parentNode = modelGraph.nodesById[node.parentId ?? ''];
  return !isGroupNode(parentNode) || parentNode.expanded;
}
