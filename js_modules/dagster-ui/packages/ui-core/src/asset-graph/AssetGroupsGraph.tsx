import {Box, Colors, Icon} from '@dagster-io/ui-components';
import dagre from 'dagre';
import countBy from 'lodash/countBy';
import groupBy from 'lodash/groupBy';
import React from 'react';
import styled from 'styled-components';

import {withMiddleTruncation} from '../app/Util';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';

import {AssetEdges} from './AssetEdges';
import {AssetDescription, AssetName, NameTooltipStyle} from './AssetNode';
import {GraphData, GraphNode} from './Utils';
import {AssetLayout, AssetLayoutEdge} from './layout';

type GroupNode = {
  key: string;
  assets: GraphNode[];
  assetCount: number;
  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;
  name: string;
  upstream: {
    [groupKey: string]: number;
  };
  downstream: {
    [groupKey: string]: number;
  };
};

export const AssetGroupsGraph: React.FC<{data: GraphData}> = ({data}) => {
  const [highlighted, setHighlighted] = React.useState<string | null>(null);
  const viewportEl = React.useRef<SVGViewport>();

  const groups: {[groupKey: string]: GroupNode} = React.useMemo(() => {
    const groupKey = (n: GraphNode) =>
      `${n.definition.repository.location.name}:${n.definition.repository.name}:${n.definition.groupName}`;
    const assetsByGroup = groupBy(Object.values(data.nodes), groupKey);
    const groupKeyForAssetId = Object.fromEntries(
      Object.entries(data.nodes).map(([id, node]) => [id, groupKey(node)]),
    );

    return Object.fromEntries(
      Object.entries(assetsByGroup).map(([key, assets]) => [
        key,
        {
          key,
          assets,
          assetCount: assets.length,
          repository: assets[0]!.definition.repository,
          name: assets[0]!.definition.groupName || '',
          groupName: assets[0]!.definition.groupName || '',
          repositoryName: assets[0]!.definition.repository.name,
          repositoryLocationName: assets[0]!.definition.repository.location.name,
          upstream: countBy(
            assets
              .flatMap((a) => Object.keys(data.upstream[a.id] || {}))
              .map((id) => groupKeyForAssetId[id]),
          ),
          downstream: countBy(
            assets
              .flatMap((a) => Object.keys(data.downstream[a.id] || {}))
              .map((id) => groupKeyForAssetId[id]),
          ),
        },
      ]),
    );
  }, [data]);

  const layout = React.useMemo(() => buildAssetGroupsLayout(Object.values(groups)), [groups]);

  return (
    <SVGViewport
      ref={(r) => (viewportEl.current = r || undefined)}
      defaultZoom="zoom-to-fit"
      interactor={SVGViewport.Interactors.PanAndZoom}
      graphWidth={layout.width}
      graphHeight={layout.height}
      onClick={() => {}}
      onDoubleClick={(e) => {
        viewportEl.current?.autocenter(true);
        e.stopPropagation();
      }}
      maxZoom={DEFAULT_MAX_ZOOM}
      maxAutocenterZoom={1.0}
    >
      {(_, viewport) => (
        <SVGContainer width={layout.width} height={layout.height}>
          <AssetEdges
            selected={null}
            viewportRect={viewport}
            highlighted={highlighted}
            edges={layout.edges}
            strokeWidth={4}
            baseColor={Colors.KeylineGray}
          />

          {Object.values(layout.nodes)
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => (
              <foreignObject
                key={group.id}
                {...group.bounds}
                onDoubleClick={(e) => {
                  if (!viewportEl.current) {
                    return;
                  }
                  const targetScale = viewportEl.current.scaleForSVGBounds(
                    group.bounds.width,
                    group.bounds.height,
                  );
                  viewportEl.current.zoomToSVGBox(group.bounds, true, targetScale * 0.9);
                  e.stopPropagation();
                }}
              >
                <CollapsedGroupNode group={groups[group.id]!} />
              </foreignObject>
            ))}
        </SVGContainer>
      )}
    </SVGViewport>
  );
};

export const CollapsedGroupNode: React.FC<{
  group: {
    assetCount: number;
    groupName: string;
    repositoryName: string;
    repositoryLocationName: string;
  };
}> = ({group}) => {
  const name = `${group.groupName} `;
  return (
    <CollapsedGroupNodeContainer $selected={false}>
      <CollapsedGroupNodeBox $selected={false}>
        <Box style={{padding: '6px 8px'}} flex={{direction: 'row', gap: 4}} border="top">
          <span style={{marginTop: 1}}>
            <Icon name="asset_group" />
          </span>
          <div
            data-tooltip={name}
            data-tooltip-style={NameTooltipStyle}
            style={{overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: 600}}
          >
            {withMiddleTruncation(name, {maxLength: 35})}
          </div>
          <div style={{flex: 1}} />
        </Box>
        <Box style={{padding: '6px 8px'}} flex={{direction: 'column', gap: 4}} border="top">
          {withMiddleTruncation(`${group.repositoryName}@${group.repositoryLocationName}`, {
            maxLength: 35,
          })}
        </Box>
        <Box style={{padding: '6px 8px'}} flex={{direction: 'column', gap: 4}} border="top">
          <AssetDescription $color={Colors.Gray400}>{group.assetCount} assets</AssetDescription>
        </Box>
      </CollapsedGroupNodeBox>
    </CollapsedGroupNodeContainer>
  );
};

const CollapsedGroupNodeContainer = styled.div<{$selected: boolean}>`
  user-select: none;
  cursor: default;
  padding: 4px;
`;

const CollapsedGroupNodeBox = styled.div<{$selected: boolean}>`
  border: 2px solid ${(p) => (p.$selected ? Colors.Blue500 : Colors.Gray200)};
  outline: 3px solid ${(p) => (p.$selected ? Colors.Gray200 : 'transparent')};

  background: ${Colors.White};
  border-radius: 8px;
  position: relative;
  &:hover {
    box-shadow: rgba(0, 0, 0, 0.12) 0px 2px 12px 0px;
  }
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;

const MARGIN = 100;

function buildAssetGroupsLayout(groups: GroupNode[]) {
  const g = new dagre.graphlib.Graph();

  g.setGraph({
    rankdir: 'LR',
    marginx: MARGIN,
    marginy: MARGIN,
    nodesep: 10,
    edgesep: 10,
    ranksep: 60,
  });
  g.setDefaultEdgeLabel(() => ({}));

  groups.forEach((group) => g.setNode(group.key, {width: 300, height: 60}));
  groups.forEach((group) => {
    for (const [downstreamKey, downstreamDepCount] of Object.entries(group.downstream)) {
      if (downstreamKey !== group.key) {
        g.setEdge({v: group.key, w: downstreamKey}, {weight: downstreamDepCount});
        console.log(group.key, downstreamKey);
      }
    }
  });

  dagre.layout(g);

  let maxWidth = 0;
  let maxHeight = 0;

  const nodes: {[id: string]: AssetLayout} = {};

  g.nodes().forEach((id) => {
    const dagreNode = g.node(id);
    if (!dagreNode) {
      return;
    }
    const bounds = {
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
      width: dagreNode.width,
      height: dagreNode.height,
    };
    nodes[id] = {id, bounds};

    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width / 2);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height / 2);
  });

  const edges: AssetLayoutEdge[] = [];

  g.edges().forEach((e) => {
    const v = g.node(e.v);
    const w = g.node(e.w);

    // Ignore the coordinates from dagre and use the top left + bottom left of the
    edges.push({
      from: {x: v.x + v.width / 2, y: v.y},
      fromId: e.v,
      to: {x: w.x - w.width / 2 - 5, y: w.y},
      toId: e.w,
    });
  });

  return {
    nodes,
    edges,
    width: maxWidth + MARGIN,
    height: maxHeight + MARGIN,
  };
}
