import {Colors} from '@dagster-io/ui-components';
import {useWorker} from '@koale/useworker';
import {Fragment, memo, useEffect, useRef, useState} from 'react';

import {buildSVGPathHorizontal, buildSVGPathVertical} from './Utils';
import {AssetLayoutDirection, AssetLayoutEdge} from './layout';
import {useUpdatingRef} from '../hooks/useUpdatingRef';

interface AssetEdgesProps {
  edges: AssetLayoutEdge[];
  selected: string[] | null;
  highlighted: string[] | null;
  direction: AssetLayoutDirection;
  strokeWidth?: number;
  viewportRect: {top: number; left: number; right: number; bottom: number};
}

function getEdgesToShow({
  viewportRect,
  highlighted,
  selected,
  edges,
}: Pick<AssetEdgesProps, 'viewportRect' | 'selected' | 'edges' | 'highlighted'>) {
  try {
    const viewportDistance =
      Math.pow(viewportRect.right - viewportRect.left, 2) +
      Math.pow(viewportRect.top - viewportRect.bottom, 2);
    const MAX_EDGES = 50; // arbitrary number

    //https://stackoverflow.com/a/20925869/1162881
    function doesViewportContainEdge(
      edge: {from: {x: number; y: number}; to: {x: number; y: number}},
      viewportRect: {top: number; left: number; right: number; bottom: number},
    ) {
      return (
        isOverlapping1D(
          Math.max(edge.from.x, edge.to.x),
          Math.max(viewportRect.left, viewportRect.right),
          Math.min(edge.from.x, edge.to.x),
          Math.min(viewportRect.left, viewportRect.right),
        ) &&
        isOverlapping1D(
          Math.max(edge.from.y, edge.to.y),
          Math.max(viewportRect.top, viewportRect.bottom),
          Math.min(edge.from.y, edge.to.y),
          Math.min(viewportRect.top, viewportRect.bottom),
        )
      );
    }

    function isOverlapping1D(xmax1: number, xmax2: number, xmin1: number, xmin2: number) {
      return xmax1 >= xmin2 && xmax2 >= xmin1;
    }

    function doesViewportContainPoint(
      point: {x: number; y: number},
      viewportRect: {top: number; left: number; right: number; bottom: number},
    ) {
      return (
        point.x >= viewportRect.left &&
        point.x <= viewportRect.right &&
        point.y >= viewportRect.top &&
        point.y <= viewportRect.bottom
      );
    }

    const edgesToShow = (() => {
      const intersectedEdges = edges.filter((edge) => doesViewportContainEdge(edge, viewportRect));
      if (intersectedEdges.length <= 10) {
        return intersectedEdges;
      }
      const visibleToAndFromEdges = new Set(
        intersectedEdges.filter(
          (edge) =>
            doesViewportContainPoint(edge.from, viewportRect) &&
            doesViewportContainPoint(edge.to, viewportRect),
        ),
      );
      const visibleToFromEdges = intersectedEdges.filter(
        (edge) =>
          doesViewportContainPoint(edge.from, viewportRect) ||
          doesViewportContainPoint(edge.to, viewportRect),
      );
      if (visibleToFromEdges.length < 50) {
        return visibleToFromEdges;
      }
      const center = {
        x: (viewportRect.left + viewportRect.right) / 2,
        y: (viewportRect.top + viewportRect.bottom) / 2,
      };
      const edgesWithDistance = visibleToFromEdges.map((edge) => {
        const distance = Math.min(
          Math.pow(edge.from.x - center.x, 2) + Math.pow(edge.from.y - center.y, 2),
          Math.pow(edge.to.x - center.x, 2) + Math.pow(edge.to.y - center.y, 2),
        );

        return {
          edge,
          // Effectively sorts edges with both nodes visible to the front.
          distance: visibleToAndFromEdges.has(edge) ? distance : viewportDistance + distance,
        };
      });
      edgesWithDistance.sort((a, b) => a.distance - b.distance);
      return edgesWithDistance.slice(0, MAX_EDGES).map((item) => item.edge);
    })();

    const selectedSet = new Set(selected ?? []);
    const highlightedSet = new Set(highlighted ?? []);

    const selectedOrHighlightedEdges = (() => {
      const selectedOrHighlighted = edges.filter(
        ({fromId, toId}) =>
          selectedSet.has(fromId) ||
          selectedSet.has(toId) ||
          highlightedSet.has(fromId) ||
          highlightedSet.has(toId),
      );
      const center = {
        x: (viewportRect.left + viewportRect.right) / 2,
        y: (viewportRect.top + viewportRect.bottom) / 2,
      };
      const edgesWithDistance = selectedOrHighlighted.map((edge) => {
        return {
          edge,
          distance: Math.min(
            Math.pow(edge.from.x - center.x, 2) + Math.pow(edge.from.y - center.y, 2),
            Math.pow(edge.to.x - center.x, 2) + Math.pow(edge.to.y - center.y, 2),
          ),
        };
      });
      edgesWithDistance.sort((a, b) => a.distance - b.distance);
      return edgesWithDistance.slice(0, MAX_EDGES).map((item) => item.edge);
    })();
    return {edgesToShow, selectedOrHighlightedEdges};
  } catch (e) {
    console.error(e);
    return {edgesToShow: [], selectedOrHighlightedEdges: []};
  }
}

type EdgeState = {edgesToShow: AssetLayoutEdge[]; selectedOrHighlightedEdges: AssetLayoutEdge[]};
export const AssetEdges = ({
  edges,
  selected,
  highlighted,
  direction,
  strokeWidth = 4,
  viewportRect,
}: AssetEdgesProps) => {
  const [getEdgesToShowWorker] = useWorker(getEdgesToShow);

  const [{edgesToShow, selectedOrHighlightedEdges}, setEdges] = useState<EdgeState>({
    edgesToShow: [],
    selectedOrHighlightedEdges: [],
  });

  const isRunning = useRef(false);
  const needsUpdate = useRef(false);
  const currentStateRef = useUpdatingRef({highlighted, edges, selected, viewportRect});
  useEffect(() => {
    if (!isRunning.current) {
      (async () => {
        needsUpdate.current = true;
        isRunning.current = true;
        while (needsUpdate.current) {
          needsUpdate.current = false;
          const edgesToShow = await new Promise<EdgeState>((res) => {
            getEdgesToShowWorker(currentStateRef.current).then((edgesToShow) => {
              res(edgesToShow);
            });
          });
          setEdges(edgesToShow);
        }
        isRunning.current = false;
      })();
    } else {
      needsUpdate.current = true;
    }
  }, [edges, getEdgesToShowWorker, highlighted, selected, viewportRect, currentStateRef]);

  // Show up to 50 edges....
  return (
    <Fragment>
      <AssetEdgeSet
        color={Colors.lineageEdge()}
        edges={edgesToShow}
        strokeWidth={strokeWidth}
        direction={direction}
      />
      <AssetEdgeSet
        color={Colors.lineageEdgeHighlighted()}
        edges={selectedOrHighlightedEdges}
        strokeWidth={strokeWidth}
        direction={direction}
      />
    </Fragment>
  );
};

interface AssetEdgeSetProps {
  edges: AssetLayoutEdge[];
  color: string;
  direction: AssetLayoutDirection;
  strokeWidth: number;
}

const AssetEdgeSet = memo(({edges, color, strokeWidth, direction}: AssetEdgeSetProps) => (
  <>
    <defs>
      <marker
        id={`arrow${btoa(color)}`}
        viewBox="0 0 8 10"
        refX="1"
        refY="5"
        markerUnits="strokeWidth"
        markerWidth={strokeWidth}
        orient="auto"
      >
        <path d="M 0 0 L 8 5 L 0 10 z" fill={color} />
      </marker>
    </defs>
    {edges.map((edge, idx) => (
      <path
        key={idx}
        d={
          direction === 'horizontal'
            ? buildSVGPathHorizontal({source: edge.from, target: edge.to})
            : buildSVGPathVertical({source: edge.from, target: edge.to})
        }
        stroke={color}
        strokeWidth={strokeWidth}
        fill="none"
        markerEnd={`url(#arrow${btoa(color)})`}
      />
    ))}
  </>
));
