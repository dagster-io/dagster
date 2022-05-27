import {Box, Colors, FontFamily, Heading, PageHeader} from '@dagster-io/ui';
import dagre from 'dagre';
import flatMap from 'lodash/flatMap';
import keyBy from 'lodash/keyBy';
import uniqBy from 'lodash/uniqBy';
import * as React from 'react';
import {useParams} from 'react-router';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {AssetNodeBox, AssetNodeContainer, AssetNode} from '../asset-graph/AssetNode';
import {
  buildSVGPath,
  displayNameForAssetKey,
  GraphData,
  identifyBundles,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {useViewport} from '../gantt/useViewport';
import {
  instanceAssetsExplorerPathFromString,
  instanceAssetsExplorerPathToURL,
} from '../pipelines/PipelinePathUtils';
import {LoadingSpinner} from '../ui/Loading';
import {ReloadAllButton} from '../workspace/ReloadAllButton';

import {AssetViewModeSwitch} from './AssetViewModeSwitch';

const INSET = 20;
const PADDING = 30;

export const InstanceAssetGrid: React.FC = () => {
  const params = useParams();
  const explorerPath = instanceAssetsExplorerPathFromString(params[0]);
  const {assetGraphData} = useAssetGraphData(null, explorerPath.opsQuery || '*');

  return (
    <Box
      flex={{direction: 'column', justifyContent: 'stretch'}}
      style={{height: '100%', position: 'relative'}}
    >
      <PageHeader
        title={<Heading>Assets</Heading>}
        right={<ReloadAllButton label="Reload definitions" />}
      />
      <Box
        background={Colors.White}
        padding={{left: 24, right: 12, vertical: 8}}
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        flex={{direction: 'row', gap: 12}}
      >
        <AssetViewModeSwitch />
      </Box>
      <AssetGrid assetGraphData={assetGraphData} />
    </Box>
  );
};

interface Box {
  id: string;
  contentIds: string[];
  layout: {top: number; left: number; width: number; height: number};
}

const runMinimalDagreLayout = (
  bundles: {[prefixId: string]: string[]},
  edges: {from: string; to: string}[],
) => {
  const g = new dagre.graphlib.Graph({compound: true});

  g.setGraph({
    rankdir: 'TB',
    marginx: 0,
    marginy: 0,
    nodesep: 20,
    edgesep: 10,
    ranksep: 20,
  });
  g.setDefaultEdgeLabel(() => ({}));
  for (const [node, contentIds] of Object.entries(bundles)) {
    g.setNode(node, {width: 250, height: contentIds.length ? 40 : 108});
  }
  for (const edge of edges) {
    g.setEdge({v: edge.from, w: edge.to}, {weight: 1});
  }

  dagre.layout(g);

  const boxes = Object.entries(bundles).map(([bundleId, contentIds]) => {
    const {x, y, width, height} = g.node(bundleId);
    return {id: bundleId, contentIds, layout: {top: y, left: x, width, height}};
  });

  // Note: This is important for other algorithms we run later, but we want to
  // do it in the layer that is cached.
  boxes.sort((a, b) => a.id.localeCompare(b.id));

  return {boxes};
};

function alignToGrid(boxes: Box[], viewportWidth: number) {
  if (viewportWidth === 0) {
    return;
  }
  // Make Dagre's layout more "grid compatible" by centering each row and
  // wrapping rows so they don't scroll offscreen
  const splitWidth = viewportWidth - 40;
  const itemsPerRow = Math.round(splitWidth / 280);
  const itemWidth = (splitWidth - (itemsPerRow - 1) * PADDING) / itemsPerRow;

  const rows: {top: number; items: Box[]}[] = [];
  for (const box of boxes) {
    if (rows[rows.length - 1]?.top === box.layout.top) {
      rows[rows.length - 1].items.push(box);
    } else {
      rows.push({items: [box], top: box.layout.top});
    }
  }

  let x = -1;
  let y = INSET;

  for (const {items} of rows) {
    const centeringOffset =
      items.length < itemsPerRow ? (splitWidth - items.length * (itemWidth + PADDING)) / 2 : 0;

    for (const box of items) {
      x++;
      if (x >= itemsPerRow) {
        y += box.layout.height + PADDING;
        x = 0;
      }
      box.layout.width = itemWidth;
      box.layout.left = INSET + centeringOffset + x * (itemWidth + PADDING);
      box.layout.top = y;
    }
    y += items[0].layout.height + PADDING;
    x = -1;
  }
}

function flattenToGrid(boxes: Box[], viewportWidth: number) {
  if (viewportWidth === 0) {
    return;
  }
  // Try to arrange the bundles so the downstream ones are generally lower in the grid.
  // Algorithm: Iterate through the folders and insert each into the result set such that
  // it is before things that depend on it and after things that it depends on.
  // If we can't satisfy these (bi-directional deps are possible), we put at the midpoint.

  const splitWidth = viewportWidth - 40;
  const itemsPerRow = Math.round(splitWidth / 280);
  const itemWidth = (splitWidth - (itemsPerRow - 1) * PADDING) / itemsPerRow;

  let x = -1;
  let y = INSET;
  const centeringOffset =
    boxes.length < itemsPerRow ? (splitWidth - boxes.length * (itemWidth + PADDING)) / 2 : 0;

  boxes.forEach((box) => {
    x++;
    if (x >= itemsPerRow) {
      x = 0;
      y += box.layout.height + PADDING;
    }
    box.layout.top = y;
    box.layout.left = INSET + centeringOffset + x * (itemWidth + PADDING);
    box.layout.width = itemWidth;
  });
}

function expandBoxes(layout: Layout, expanded: string | null, viewportWidth: number) {
  // Find the box we want to expand
  const boxIdx = layout.boxes.findIndex((b) => b.id === expanded);
  if (boxIdx === -1) {
    return {boxes: layout.boxes, shadows: []};
  }

  const boxes: Box[] = JSON.parse(JSON.stringify(layout.boxes));
  const box = boxes[boxIdx]!;
  const shadow = {
    top: box.layout.top + box.layout.height + PADDING / 2,
    height: 0,
  };
  const toPushDown = boxes.filter((b) => b.layout.top >= shadow.top);

  const contentsWithChildren: {[id: string]: string[]} = {};
  box.contentIds.forEach((c) => (contentsWithChildren[c] = []));

  const contentsEdges = uniqBy(
    layout.edges
      .filter((e) => contentsWithChildren[e.from] && contentsWithChildren[e.to])
      .map((e) => ({
        from: contentsWithChildren[e.from] ? e.from : layout.bundleForAssetId[e.from],
        to: contentsWithChildren[e.to] ? e.to : layout.bundleForAssetId[e.to],
      })),
    JSON.stringify,
  );
  const contents =
    contentsEdges.length > 0 && box.contentIds.length < 100
      ? runMinimalDagreLayout(contentsWithChildren, contentsEdges)
      : {
          boxes: Object.entries(contentsWithChildren).map(([bundleId, contentIds]) => ({
            id: bundleId,
            contentIds,
            layout: {top: 0, left: 0, width: 250, height: 108},
          })),
        };

  if (contentsEdges.length === 0 || contents.boxes.length > 10) {
    flattenToGrid(contents.boxes, viewportWidth);
  } else {
    alignToGrid(contents.boxes, viewportWidth);
  }

  // Add the nodes for the childern
  boxes.splice(boxIdx, 0, ...contents.boxes);
  for (const box of contents.boxes) {
    box.layout.top += shadow.top;
  }

  // Push the nodes beneath the shadow down
  const contentBottom = Math.max(...contents.boxes.map((b) => b.layout.top + b.layout.height));
  shadow.height = contentBottom - shadow.top + PADDING / 2;
  toPushDown.forEach((box) => (box.layout.top += shadow.height));

  return {boxes, shadows: [shadow]};
}

type Layout = ReturnType<typeof useAssetGridLayout>;

const NONE_BUNDLE = '["none"]';

function useAssetGridLayout(assetGraphData: GraphData | null, viewportWidth: number) {
  return React.useMemo(() => {
    if (!assetGraphData) {
      return {bundles: {}, bundleForAssetId: {}, boxes: [], edges: []};
    }

    const assetIds = Object.keys(assetGraphData.nodes);
    const bundles = identifyBundles(assetIds);
    const bundleForAssetId: {[assetId: string]: string} = {};
    for (const [bundleId, childrenIds] of Object.entries(bundles)) {
      childrenIds.forEach((c) => (bundleForAssetId[c] = bundleId));
    }

    const unbundledAssetIds = assetIds.filter((id) => !bundleForAssetId[id]);
    if (unbundledAssetIds.length) {
      bundles[NONE_BUNDLE] = unbundledAssetIds;
      bundles[NONE_BUNDLE].forEach((id) => (bundleForAssetId[id] = NONE_BUNDLE));
    }

    const edges = flatMap(Object.entries(assetGraphData.downstream), ([from, downstreams]) =>
      Object.keys(downstreams).map((to) => ({from, to})),
    );

    const {boxes} = runMinimalDagreLayout(
      bundles,
      uniqBy(
        edges.map((e) => ({from: bundleForAssetId[e.from], to: bundleForAssetId[e.to]})),
        JSON.stringify,
      ),
    );
    if (boxes.length > 10) {
      flattenToGrid(boxes, viewportWidth);
    } else {
      alignToGrid(boxes, viewportWidth);
    }

    return {bundles, bundleForAssetId, boxes, edges};
  }, [assetGraphData, viewportWidth]);
}

const AssetGrid: React.FC<{
  assetGraphData: GraphData | null;
}> = ({assetGraphData}) => {
  const [highlighted, setHighlighted] = React.useState<string | null>(null);
  const [expanded, setExpanded] = React.useState<string | null>(null);
  const {viewport, containerProps} = useViewport();
  const layout = useAssetGridLayout(assetGraphData, viewport.width);
  const {edges, bundleForAssetId} = layout;
  const {boxes, shadows} = React.useMemo(() => expandBoxes(layout, expanded, viewport.width), [
    layout,
    expanded,
    viewport.width,
  ]);

  const expandedAssetKeys =
    boxes.find((b) => b.id === expanded)?.contentIds.map((id) => ({path: JSON.parse(id)})) || [];

  const {liveResult, liveDataByNode} = useLiveDataForAssetKeys(
    undefined,
    assetGraphData?.nodes,
    expandedAssetKeys,
  );

  useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

  if (!assetGraphData) {
    return <LoadingSpinner purpose="page" />;
  }

  const renderedIds = keyBy(
    boxes.filter((b) => expanded !== b.id),
    (b) => b.id,
  );
  const renderedEdges = uniqBy(
    edges.map((e) => ({
      from: renderedIds[e.from] ? e.from : bundleForAssetId[e.from] || e.from,
      to: renderedIds[e.to] ? e.to : bundleForAssetId[e.to] || e.to,
    })),
    JSON.stringify,
  );

  const bottom = Math.max(
    ...shadows.map((s) => s.top + s.height),
    ...boxes.map((b) => b.layout.top + b.layout.height),
  );

  return (
    <div
      {...containerProps}
      style={{
        overflowY: 'scroll',
        position: 'relative',
        width: '100%',
        height: bottom,
      }}
    >
      {shadows.map((shadow) => (
        <div
          key={shadow.top}
          style={{
            position: 'absolute',
            background: '#FDF6EF',
            boxShadow: `inset 0 2px 4px rgba(0,0,0,0.15)`,
            borderBottom: `1px solid rgba(0,0,0,0.15)`,
            top: shadow.top,
            height: shadow.height,
            left: 0,
            right: 0,
          }}
        />
      ))}
      <div style={{position: 'absolute', zIndex: 1}}>
        {boxes
          .filter((b) => !b.contentIds.length)
          .map((box) => (
            <div
              key={box.id}
              style={{position: 'absolute', ...box.layout}}
              onMouseEnter={() => setHighlighted(box.id)}
              onMouseLeave={() => setHighlighted(null)}
            >
              <AssetNode
                definition={assetGraphData.nodes[box.id].definition}
                selected={false}
                padded={false}
                liveData={liveDataByNode[box.id]}
              />
            </div>
          ))}
      </div>
      <AssetGridEdges
        boxes={boxes}
        highlighted={highlighted}
        edges={renderedEdges}
        expanded={expanded}
      />
      <div style={{position: 'absolute', zIndex: 2}}>
        {boxes
          .filter((b) => b.contentIds.length)
          .map((box) => (
            <AssetGridItem
              key={box.id}
              box={box}
              highlighted={highlighted === box.id}
              setHighlighted={setHighlighted}
              expanded={expanded === box.id}
              toggleExpanded={() => setExpanded(expanded === box.id ? null : box.id)}
            />
          ))}
      </div>
    </div>
  );
};

const AssetGridEdges = ({
  boxes,
  edges,
  highlighted,
  expanded,
}: {
  boxes: Box[];
  highlighted: string | null;
  expanded: string | null;
  edges: {from: string; to: string}[];
}) => {
  const highlightedEdges =
    highlighted && highlighted !== expanded
      ? edges.filter((e) => e.from === highlighted || e.to === highlighted)
      : [];

  const expandedChildren = boxes.find((b) => b.id === expanded)?.contentIds || [];
  const expandedEdges = edges.filter(
    (e) => expandedChildren.includes(e.from) || expandedChildren.includes(e.to),
  );

  const showBaseEdgeHintsAlways = expandedEdges.length === 0; // && boxes.length < 30
  const showExpandedEdgeHintsAlways = expandedEdges.length > 0;

  const width = Math.max(...boxes.map((b) => b.layout.width + b.layout.left));
  const height = Math.max(...boxes.map((b) => b.layout.height + b.layout.top));

  return (
    <React.Fragment>
      {showBaseEdgeHintsAlways && (
        <StyledPathSet
          key="base"
          boxes={boxes}
          edges={edges}
          color="rgba(35, 31, 27, 0.06)"
          zIndex={0}
          width={width}
          height={height}
        />
      )}

      {showExpandedEdgeHintsAlways && (
        <StyledPathSet
          key="expanded"
          boxes={boxes}
          edges={expandedEdges}
          color="rgba(35, 31, 27, 0.06)"
          zIndex={0}
          width={width}
          height={height}
        />
      )}

      {highlightedEdges.length > 0 && (
        <StyledPathSet
          key="highlighted-to"
          boxes={boxes}
          edges={highlightedEdges.filter((e) => e.to === highlighted)}
          color={Colors.Olive500}
          zIndex={1}
          width={width}
          height={height}
        />
      )}
      {highlightedEdges.length > 0 && (
        <StyledPathSet
          key="highlighted-from"
          boxes={boxes}
          edges={highlightedEdges.filter((e) => e.from === highlighted)}
          color={Colors.Blue500}
          zIndex={1}
          width={width}
          height={height}
        />
      )}
    </React.Fragment>
  );
};

const StyledPathSet: React.FC<{
  boxes: Box[];
  edges: {from: string; to: string}[];
  color: string;
  zIndex: number;
  width: number;
  height: number;
}> = React.memo(({boxes, edges, color, zIndex, width, height}) => {
  const pointForAssetId = (bundleId: string) => {
    const box = boxes.find((b) => b.id === bundleId);
    if (!box) {
      console.log(bundleId);
      return {x: 0, y: 0};
    }
    const {width, height, left, top} = box.layout;
    return {x: left + width / 2, y: top + height / 2};
  };
  const stackings = {left: 0, right: 0};

  const dForEdge = (edge: {from: string; to: string}) => {
    const source = pointForAssetId(edge.from);
    source.x += boxes[0].layout.width / 2 - 24;
    const target = pointForAssetId(edge.to);
    target.x -= boxes[0].layout.width / 2 - 24;

    if (source.y < target.y) {
      target.y -= 30;
    } else if (source.y > target.y) {
      target.y += 30; //boxes[0].layout.height / 2 - stackings.bottom++ * 10;
    } else {
      if (source.x < target.x) {
        target.x -= 30;
        source.y += stackings.left;
        target.y += stackings.left;
        stackings.left += 7;
      } else if (source.x > target.x) {
        target.x += 30;
        source.y += stackings.right;
        target.y += stackings.right;
        stackings.right += 7;
      }
    }
    return buildSVGPath({source, target});
  };

  const markerId = React.useRef(`arrow${Math.random()}`);

  return (
    <svg style={{zIndex, width, height, position: 'absolute', pointerEvents: 'none'}}>
      <defs>
        <marker
          id={markerId.current}
          viewBox="0 0 8 10"
          refX="1"
          refY="5"
          markerUnits="strokeWidth"
          markerWidth="4"
          orient="auto"
        >
          <path d="M 0 0 L 8 5 L 0 10 z" fill={color} />
        </marker>
      </defs>
      {edges.map((edge, idx) => (
        <StyledPath
          key={idx}
          d={dForEdge(edge)}
          stroke={color}
          markerEnd={`url(#${markerId.current})`}
        />
      ))}
    </svg>
  );
});

const StyledPath = styled('path')`
  stroke-width: 4;
  fill: none;
`;

const AssetGridItem = ({
  box,
  expanded,
  highlighted,
  setHighlighted,
  toggleExpanded,
}: {
  box: Box;
  highlighted: boolean;
  setHighlighted: (s: string | null) => void;
  expanded: boolean;
  toggleExpanded: () => void;
}) => {
  return (
    <AssetNodeContainer
      $selected={false}
      $padded={false}
      style={{
        margin: 0,
        position: 'absolute',
        background: 'transparent',
        outline: expanded ? `10px solid #FDF6EF` : 'none',
        boxShadow: expanded ? `0px 15px 0 9px #FDF6EF` : 'none',
        ...box.layout,
      }}
      onMouseEnter={() => setHighlighted(box.id)}
      onMouseLeave={() => setHighlighted(null)}
      onClick={() => toggleExpanded()}
    >
      <AssetNodeBox
        style={expanded ? {background: Colors.Gray100, border: `2px solid ${Colors.Gray200}`} : {}}
        $selected={false}
      >
        <div
          style={{
            width: 16,
            height: 16,
            left: 10,
            top: 10,
            borderRadius: 8,
            position: 'absolute',
            background: highlighted ? Colors.Olive500 : Colors.LightPurple,
          }}
        />
        <div
          style={{
            width: 16,
            height: 16,
            right: 10,
            top: 10,
            borderRadius: 8,
            position: 'absolute',
            background: highlighted ? Colors.Blue500 : Colors.LightPurple,
          }}
        />

        <div style={{paddingLeft: 30}}>
          <div style={{fontFamily: FontFamily.monospace, fontWeight: 600}}>
            {displayNameForAssetKey({path: JSON.parse(box.id)})}
          </div>
          <div style={{display: 'flex', gap: 8}}>
            <div> {box.contentIds.length} items</div>
            <Link
              to={instanceAssetsExplorerPathToURL({
                opsQuery: `${tokenForAssetKey({path: JSON.parse(box.id)})}>`,
                opNames: [],
              })}
            >
              View Graph
            </Link>
          </div>
        </div>
      </AssetNodeBox>
    </AssetNodeContainer>
  );
};
