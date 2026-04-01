import {
  Box,
  Button,
  Checkbox,
  Colors,
  ErrorBoundary,
  Icon,
  NonIdealState,
  Spinner,
  SplitPanelContainer,
  Tooltip,
} from '@dagster-io/ui-components';
import {observeEnabled} from '@shared/app/observeEnabled';
import {AssetSelectionInput} from '@shared/asset-selection/input/AssetSelectionInput';
import {CreateCatalogViewButton} from '@shared/assets/CreateCatalogViewButton';
import {useCatalogExtraDropdownOptions} from '@shared/assets/catalog/useCatalogExtraDropdownOptions';
import pickBy from 'lodash/pickBy';
import throttle from 'lodash/throttle';
import uniq from 'lodash/uniq';
import without from 'lodash/without';
import {ParsedQs} from 'qs';
import * as React from 'react';
import {useCallback, useMemo, useRef, useState} from 'react';
import styled from 'styled-components';

import {AssetEdges} from './AssetEdges';
import {AssetGraphBackgroundContextMenu} from './AssetGraphBackgroundContextMenu';
import {AssetGraphJobSidebar} from './AssetGraphJobSidebar';
import {AssetNode, AssetNodeContextMenuWrapper, AssetNodeMinimal} from './AssetNode';
import {AssetNodeFacetSettingsButton} from './AssetNodeFacetSettingsButton';
import {useSavedAssetNodeFacets} from './AssetNodeFacets';
import {AssetNodeMenuProps} from './AssetNodeMenu';
import {CollapsedGroupNode} from './CollapsedGroupNode';
import {ExpandedGroupNode, GroupOutline} from './ExpandedGroupNode';
import {AssetNodeLink} from './ForeignNode';
import {AssetGraphSettingsButton, useLayoutDirectionState} from './GraphSettings';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  AssetGraphViewType,
  GraphData,
  GraphNode,
  groupIdForNode,
  isGroupId,
  tokenForAssetKey,
} from './Utils';
import {applyPositionOverrides} from './applyLayoutOverrides';
import {assetKeyTokensInRange} from './assetKeyTokensInRange';
import {getGroupBoundsForRender} from './groupRenderUtils';
import {AssetGraphLayout, GroupLayout, computeEdgeEndpoints} from './layout';
import {getGroupManualPositionState} from './manualPositionState';
import {getPositionOverrideKey} from './positionOverrideKey';
import {AssetGraphExplorerSidebar} from './sidebar/Sidebar';
import {AssetGraphQueryItem} from './types';
import {AssetGraphFetchScope, useAssetGraphData, useFullAssetGraphData} from './useAssetGraphData';
import {AssetLocation, useFindAssetLocation} from './useFindAssetLocation';
import {useNodeDrag} from './useNodeDrag';
import {usePositionOverrides} from './usePositionOverrides';
import {useFullScreen, useFullScreenAllowedView} from '../app/AppTopNav/AppTopNavContext';
import {useFeatureFlags} from '../app/useFeatureFlags';
import {AssetLiveDataRefreshButton} from '../asset-data/AssetLiveDataProvider';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {DEFAULT_MAX_ZOOM} from '../graph/SVGConsts';
import {SVGViewport, SVGViewportRef} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {closestNodeInDirection, isNodeOffscreen} from '../graph/common';
import {usePreviousDistinctValue} from '../hooks/usePrevious';
import {useQueryAndLocalStoragePersistedState} from '../hooks/useQueryAndLocalStoragePersistedState';
import {
  GraphExplorerOptions,
  OptionsOverlay,
  RightInfoPanel,
  RightInfoPanelContent,
} from '../pipelines/GraphExplorer';
import {
  CycleDetectedNotice,
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  InvalidSelectionQueryNotice,
  LargeDAGNotice,
  LoadingContainer,
  LoadingNotice,
} from '../pipelines/GraphNotices';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {SyntaxError} from '../selection/CustomErrorListener';
import {IndeterminateLoadingBar} from '../ui/IndeterminateLoadingBar';
import {LoadingSpinner} from '../ui/Loading';
import {isIframe} from '../util/isIframe';
import {buildRepoPathForHuman} from '../workspace/buildRepoAddress';

type Props = {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  fetchOptions: AssetGraphFetchScope;

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToSourceAssetNode: (
    e: Pick<React.MouseEvent<any>, 'metaKey'>,
    node: AssetLocation,
  ) => void;
  viewType: AssetGraphViewType;
  setHideEdgesToNodesOutsideQuery?: (hideEdgesToNodesOutsideQuery: boolean) => void;
};

export const MINIMAL_SCALE = 0.6;
export const GROUPS_ONLY_SCALE = 0.15;

export const AssetGraphExplorer = React.memo((props: Props) => {
  const {fullAssetGraphData: currentFullAssetGraphData} = useFullAssetGraphData(props.fetchOptions);
  const previousFullAssetGraphData = usePreviousDistinctValue(currentFullAssetGraphData);

  const fullAssetGraphData = currentFullAssetGraphData ?? previousFullAssetGraphData;

  const {
    loading: graphDataLoading,
    assetGraphData: currentAssetGraphData,
    graphQueryItems: currentGraphQueryItems,
    allAssetKeys: currentAllAssetKeys,
  } = useAssetGraphData(props.explorerPath.opsQuery, props.fetchOptions);

  const previousAssetGraphData = usePreviousDistinctValue(currentAssetGraphData);
  const previousGraphQueryItems = usePreviousDistinctValue(currentGraphQueryItems);
  const previousAllAssetKeys = usePreviousDistinctValue(currentAllAssetKeys);

  const assetGraphData = currentAssetGraphData ?? previousAssetGraphData;
  const graphQueryItems = currentGraphQueryItems ?? previousGraphQueryItems;
  const allAssetKeys = currentAllAssetKeys ?? previousAllAssetKeys;

  if (graphDataLoading && (!assetGraphData || !allAssetKeys)) {
    return <LoadingSpinner purpose="page" />;
  }

  if (!assetGraphData || !allAssetKeys) {
    return <NonIdealState icon="error" title="Query Error" />;
  }

  return (
    <AssetGraphExplorerWithData
      key={props.explorerPath.pipelineName}
      assetGraphData={assetGraphData}
      fullAssetGraphData={fullAssetGraphData ?? assetGraphData}
      allAssetKeys={allAssetKeys}
      graphQueryItems={graphQueryItems}
      loading={graphDataLoading}
      {...props}
    />
  );
});

type WithDataProps = Props & {
  allAssetKeys: AssetKey[];
  assetGraphData: GraphData;
  fullAssetGraphData: GraphData;
  graphQueryItems: AssetGraphQueryItem[];
  loading: boolean;

  viewType: AssetGraphViewType;
};

const AssetGraphExplorerWithData = ({
  options,
  setOptions,
  explorerPath,
  onChangeExplorerPath,
  onNavigateToSourceAssetNode: onNavigateToSourceAssetNode,
  assetGraphData,
  fullAssetGraphData,
  graphQueryItems,
  fetchOptions,
  allAssetKeys,
  viewType,
  loading: dataLoading,
  setHideEdgesToNodesOutsideQuery,
}: WithDataProps) => {
  const findAssetLocation = useFindAssetLocation();
  const [highlighted, setHighlighted] = React.useState<string[] | null>(null);

  const {allGroups, allGroupCounts, groupedAssets} = React.useMemo(() => {
    const groupedAssets: Record<string, GraphNode[]> = {};
    Object.values(assetGraphData.nodes).forEach((node) => {
      const groupId = groupIdForNode(node);
      groupedAssets[groupId] = groupedAssets[groupId] || [];
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      groupedAssets[groupId]!.push(node);
    });
    const counts: Record<string, number> = {};
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    Object.keys(groupedAssets).forEach((key) => (counts[key] = groupedAssets[key]!.length));
    return {allGroups: Object.keys(groupedAssets), allGroupCounts: counts, groupedAssets};
  }, [assetGraphData]);

  const [direction, setDirection] = useLayoutDirectionState();
  const [facets, setFacets] = useSavedAssetNodeFacets();
  const [forceLargeGraph, setForceLargeGraph] = useState(false);

  const {flagAssetGraphGroupsPerCodeLocation} = useFeatureFlags();

  const [expandedGroups, setExpandedGroups] = useQueryAndLocalStoragePersistedState<string[]>({
    localStorageKey: `asset-graph-open-graph-nodes-${viewType}-${explorerPath.pipelineName}`,
    encode: useCallback(
      (arr: string[]) => ({expanded: arr.length ? arr.join(',') : undefined}),
      [],
    ),
    decode: useCallback((qs: ParsedQs) => {
      if (typeof qs.expanded === 'string') {
        return qs.expanded.split(',').filter(Boolean);
      }
      return [];
    }, []),
    isEmptyState: (val) => val.length === 0,
  });

  const focusGroupIdAfterLayoutRef = React.useRef('');

  const {
    layout,
    loading: layoutLoading,
    error,
    async,
  } = useAssetLayout(
    assetGraphData,
    expandedGroups,
    useMemo(
      () => ({
        direction,
        forceLargeGraph,
        flagAssetGraphGroupsPerCodeLocation,
        facets: Array.from(facets),
      }),
      [direction, facets, forceLargeGraph, flagAssetGraphGroupsPerCodeLocation],
    ),
    dataLoading,
  );

  const viewportEl = React.useRef<SVGViewportRef>();

  const positionOverrideKey = useMemo(
    () =>
      getPositionOverrideKey({
        viewType,
        explorerPath,
        fetchOptions,
      }),
    [explorerPath, fetchOptions, viewType],
  );

  const {
    overrides,
    updateNodePosition,
    updateMultiplePositions,
    resetNodePosition,
    resetMultiplePositions,
    resetAllOverrides,
    hasOverrides,
  } = usePositionOverrides(positionOverrideKey, assetGraphData, fullAssetGraphData);

  // Throttled variant for Shift+Arrow keyboard nudging. Key repeat fires at 30-50 events/sec;
  // throttling to ~10 writes/sec avoids serializing the full overrides map on every frame
  // while still feeling responsive. trailing:true ensures the final position is always committed.
  // Use a stable ref so the throttle instance is never recreated (which would drop pending
  // trailing calls). updateNodePositionRef is updated every render to always call the latest version.
  const updateNodePositionRef = useRef(updateNodePosition);
  updateNodePositionRef.current = updateNodePosition;
  const updateNodePositionThrottled = useRef(
    throttle(
      (nodeId: string, position: {x: number; y: number}) =>
        updateNodePositionRef.current(nodeId, position),
      100,
      {leading: true, trailing: true},
    ),
  ).current;

  // Build explicit nodeId → groupId mapping for group bound recomputation
  const nodeToGroupId = useMemo(() => {
    const map: Record<string, string> = {};
    for (const [gId, nodes] of Object.entries(groupedAssets)) {
      for (const node of nodes) {
        map[node.id] = gId;
      }
    }
    return map;
  }, [groupedAssets]);

  const effectiveLayout = useMemo(
    () => (layout ? applyPositionOverrides(layout, overrides, direction, nodeToGroupId) : null),
    [layout, overrides, direction, nodeToGroupId],
  );

  // Keep a ref so the viewport-centering effect always reads the latest effectiveLayout
  // (Dagre layout + position overrides) without adding it to the effect's dependency array.
  // The effect only re-runs when the underlying Dagre `layout` changes; effectiveLayout
  // would change on every drag frame (new object each time overrides update), which would
  // cause jarring auto-recentering during drag if it were in the deps array.
  const effectiveLayoutRef = useRef(effectiveLayout);
  effectiveLayoutRef.current = effectiveLayout;

  const {onNodeMouseDown, onGroupMouseDown, draggingNodeId, draggedNodePositions} = useNodeDrag({
    layout: effectiveLayout,
    viewportRef: viewportEl,
    onCommitPosition: updateNodePosition,
    onCommitMultiplePositions: updateMultiplePositions,
  });

  // Patch edges in real-time during drag so they follow dragged nodes.
  // Works for both single-node drag and group drag (all child positions are in draggedNodePositions).
  const edgesForRender = useMemo(() => {
    if (!effectiveLayout) {
      return [];
    }
    const draggedIds = Object.keys(draggedNodePositions);
    if (draggedIds.length === 0) {
      return effectiveLayout.edges;
    }
    const draggedSet = new Set(draggedIds);
    const linkNodeSet = new Set(effectiveLayout.linkNodeIds);
    const getEdgeBounds = (id: string) =>
      effectiveLayout.nodes[id]?.bounds ?? effectiveLayout.groups[id]?.bounds;

    return effectiveLayout.edges.map((edge) => {
      if (!draggedSet.has(edge.fromId) && !draggedSet.has(edge.toId)) {
        return edge;
      }
      const fromPos = draggedNodePositions[edge.fromId];
      const toPos = draggedNodePositions[edge.toId];
      const baseFrom = getEdgeBounds(edge.fromId);
      const fromBounds = fromPos && baseFrom ? {...baseFrom, x: fromPos.x, y: fromPos.y} : baseFrom;
      const baseTo = getEdgeBounds(edge.toId);
      const toBounds = toPos && baseTo ? {...baseTo, x: toPos.x, y: toPos.y} : baseTo;
      if (!fromBounds || !toBounds) {
        return edge;
      }
      const fromXInset = linkNodeSet.has(edge.fromId) ? 16 : 24;
      const toXInset = linkNodeSet.has(edge.toId) ? 16 : 24;
      const {from, to} = computeEdgeEndpoints(
        fromBounds,
        toBounds,
        direction,
        fromXInset,
        toXInset,
      );
      return {...edge, from, to};
    });
  }, [draggedNodePositions, effectiveLayout, direction]);

  const selectedTokens =
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    explorerPath.opNames[explorerPath.opNames.length - 1]!.split(',').filter(Boolean);
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedTokens.includes(tokenForAssetKey(node.definition.assetKey)),
  );
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const lastSelectedNode = selectedGraphNodes[selectedGraphNodes.length - 1]!;

  const selectedDefinitions = selectedGraphNodes.map((a) => a.definition);
  const allDefinitionsForMaterialize = Object.values(assetGraphData.nodes).map((a) => a.definition);

  const onSelectNode = React.useCallback(
    async (
      e: React.MouseEvent<any> | React.KeyboardEvent<any>,
      assetKey: {path: string[]},
      node: GraphNode | null,
    ) => {
      e.stopPropagation();

      const token = tokenForAssetKey(assetKey);
      const nodeIsInDisplayedGraph = node?.definition;

      if (!nodeIsInDisplayedGraph) {
        // The asset's definition was not provided in our query for job.assetNodes. It's either
        // in another job or asset group, or is a source asset not defined in any repository.
        return onNavigateToSourceAssetNode(e, await findAssetLocation(assetKey));
      }

      // This asset is in a job and we can stay in the job graph explorer!
      // If it's in our current job, allow shift / meta multi-selection.
      let nextOpsNameSelection = token;

      if (e.shiftKey || e.metaKey) {
        // Meta key adds the node you clicked to your existing selection
        let tokensToAdd = [token];

        // Shift key adds the nodes between the node you clicked and your existing selection.
        // To better support clicking a bunch of leaves and extending selection, we try to reach
        // the new node from each node in your current selection until we find a path.
        if (e.shiftKey && selectedGraphNodes.length && node) {
          const reversed = [...selectedGraphNodes].reverse();
          for (const from of reversed) {
            const tokensInRange = assetKeyTokensInRange({from, to: node, graph: assetGraphData});
            if (tokensInRange.length) {
              tokensToAdd = tokensInRange;
              break;
            }
          }
        }

        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const existing = explorerPath.opNames[0]!.split(',');
        nextOpsNameSelection = (
          existing.includes(token) ? without(existing, token) : uniq([...existing, ...tokensToAdd])
        ).join(',');
      }

      const nextCenter = effectiveLayout?.nodes[nextOpsNameSelection.at(-1) ?? ''];
      if (nextCenter) {
        viewportEl.current?.zoomToSVGCoords(nextCenter.bounds.x, nextCenter.bounds.y, true);
      }

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [nextOpsNameSelection],
          pipelineName: explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [
      explorerPath,
      onChangeExplorerPath,
      onNavigateToSourceAssetNode,
      findAssetLocation,
      selectedGraphNodes,
      assetGraphData,
      effectiveLayout,
    ],
  );

  const zoomToGroup = React.useCallback(
    (groupId: string, animate = true, adjustScale = true) => {
      if (!viewportEl.current) {
        return;
      }
      const groupBounds = effectiveLayout && effectiveLayout.groups[groupId]?.bounds;
      if (groupBounds) {
        const targetScale = viewportEl.current.scaleForSVGBounds(
          groupBounds.width,
          groupBounds.height,
        );
        const currentScale = viewportEl.current.getScale();
        viewportEl.current.zoomToSVGBox(
          groupBounds,
          animate,
          adjustScale ? Math.min(currentScale, targetScale * 0.9) : currentScale,
          true,
        );
      }
    },
    [viewportEl, effectiveLayout],
  );

  const onChangeAssetSelection = useCallback(
    (opsQuery: string) => {
      onChangeExplorerPath({...explorerPath, opsQuery}, 'replace');
    },
    [explorerPath, onChangeExplorerPath],
  );

  const lastRenderedLayout = useRef<AssetGraphLayout | null>(null);

  React.useEffect(() => {
    if (!layout || !effectiveLayoutRef.current || !viewportEl.current) {
      return;
    }

    // After renders that result in a meaningfully new layout, autocenter or
    // focus on the selected node. (If selection was specified in the URL).
    // Don't animate this change. Use raw `layout` for change detection so that
    // user-driven position overrides don't trigger re-centering.
    // effectiveLayoutRef (not effectiveLayout) is used here so this effect doesn't
    // re-run on every drag frame — only when the underlying Dagre layout changes.
    if (layoutChangeShouldAdjustViewport(lastRenderedLayout.current, layout)) {
      if (
        focusGroupIdAfterLayoutRef.current &&
        effectiveLayoutRef.current.groups[focusGroupIdAfterLayoutRef.current]?.expanded
      ) {
        zoomToGroup(focusGroupIdAfterLayoutRef.current, false, false);
        focusGroupIdAfterLayoutRef.current = '';
      } else if (lastSelectedNode) {
        const layoutNode = effectiveLayoutRef.current.nodes[lastSelectedNode.id];
        if (layoutNode) {
          viewportEl.current.zoomToSVGBox(layoutNode.bounds, false);
        }
        viewportEl.current.focus();
      } else {
        viewportEl.current.autocenter(false);
      }
    }
    lastRenderedLayout.current = layout;
  }, [lastSelectedNode, layout, viewportEl, zoomToGroup]);

  const onClickBackground = () =>
    onChangeExplorerPath(
      {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
      'replace',
    );

  const onArrowKeyDown = (e: React.KeyboardEvent<any>, dir: 'left' | 'right' | 'up' | 'down') => {
    if (!effectiveLayout || !lastSelectedNode) {
      return;
    }

    if (e.shiftKey) {
      // Shift+Arrow: nudge the selected node's manual position by 20px
      const nodeLayout = effectiveLayout.nodes[lastSelectedNode.id];
      if (!nodeLayout) {
        return;
      }
      const NUDGE_PX = 20;
      const delta = {
        left: {x: -NUDGE_PX, y: 0},
        right: {x: NUDGE_PX, y: 0},
        up: {x: 0, y: -NUDGE_PX},
        down: {x: 0, y: NUDGE_PX},
      }[dir];
      e.preventDefault();
      updateNodePositionThrottled(lastSelectedNode.id, {
        x: nodeLayout.bounds.x + delta.x,
        y: nodeLayout.bounds.y + delta.y,
      });
      return;
    }

    const hasDefinition = (node: {id: string}) => !!assetGraphData.nodes[node.id]?.definition;
    const layoutWithoutExternalLinks = {
      ...effectiveLayout,
      nodes: pickBy(effectiveLayout.nodes, hasDefinition),
    };

    const nextId = closestNodeInDirection(layoutWithoutExternalLinks, lastSelectedNode.id, dir);
    selectNodeById(e, nextId);
  };

  const toggleSelectAllGroupNodesById = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, groupId: string) => {
      const assets = groupedAssets[groupId] || [];
      const childNodeTokens = assets.map((n) => tokenForAssetKey(n.assetKey));

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const existing = explorerPath.opNames[0]!.split(',');

      const nextOpsNameSelection = childNodeTokens.every((token) => existing.includes(token))
        ? uniq(without(existing, ...childNodeTokens)).join(',')
        : uniq([...existing, ...childNodeTokens]).join(',');

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [nextOpsNameSelection],
        },
        'replace',
      );
    },
    [groupedAssets, explorerPath, onChangeExplorerPath],
  );

  const selectGroup = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, groupId: string) => {
      zoomToGroup(groupId);
      if (e.metaKey) {
        toggleSelectAllGroupNodesById(e, groupId);
      }
    },
    [zoomToGroup, toggleSelectAllGroupNodesById],
  );

  const selectAssetNode = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, node: GraphNode) => {
      onSelectNode(e, node.assetKey, node);

      const nodeBounds = effectiveLayout && effectiveLayout.nodes[node.id]?.bounds;
      if (nodeBounds && viewportEl.current) {
        viewportEl.current.zoomToSVGBox(nodeBounds, true);
      } else {
        const groupId = groupIdForNode(node);
        if (!expandedGroups.includes(groupId)) {
          setExpandedGroups([...expandedGroups, groupId]);
        }
      }
    },
    [onSelectNode, effectiveLayout, setExpandedGroups, expandedGroups],
  );

  const selectNodeById = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId?: string) => {
      if (!nodeId) {
        return;
      }
      if (isGroupId(nodeId)) {
        selectGroup(e, nodeId);
        return;
      }
      const node = assetGraphData.nodes[nodeId];
      if (node) {
        selectAssetNode(e, node);
      }
    },
    [assetGraphData.nodes, selectGroup, selectAssetNode],
  );

  const [showSidebar, setShowSidebar] = React.useState(
    viewType === 'global' || viewType === 'catalog',
  );
  const [rightPanelHidden, setRightPanelHidden] = React.useState(false);

  const onFilterToGroup = (group: AssetGroup | GroupLayout) => {
    const filters: string[] = [`group:"${group.groupName}"`];

    if (group.repositoryName && group.repositoryLocationName) {
      const codeLocationFilter = buildRepoPathForHuman(
        group.repositoryName,
        group.repositoryLocationName,
      );
      filters.push(`code_location:"${codeLocationFilter}"`);
    }

    onChangeAssetSelection(filters.join(' and '));
  };

  const svgViewport = effectiveLayout ? (
    <SVGViewport
      ref={(r) => {
        viewportEl.current = r || undefined;
      }}
      defaultZoom="zoom-to-fit-width"
      graphWidth={effectiveLayout.width}
      graphHeight={effectiveLayout.height}
      graphHasNoMinimumZoom={false}
      additionalToolbarElements={
        <>
          <AssetGraphSettingsButton
            expandedGroups={expandedGroups}
            setExpandedGroups={setExpandedGroups}
            allGroups={allGroups}
            direction={direction}
            setDirection={setDirection}
            hideEdgesToNodesOutsideQuery={fetchOptions.hideEdgesToNodesOutsideQuery}
            setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
          />
          <AssetNodeFacetSettingsButton value={facets} onChange={setFacets} />
          {hasOverrides && (
            <Tooltip content="Reset to auto-layout">
              <Button icon={<Icon name="refresh" />} onClick={resetAllOverrides} />
            </Tooltip>
          )}
        </>
      }
      onClick={onClickBackground}
      onArrowKeyDown={onArrowKeyDown}
      onDoubleClick={(e) => {
        viewportEl.current?.autocenter(true);
        e.stopPropagation();
      }}
      maxZoom={DEFAULT_MAX_ZOOM}
      maxAutocenterZoom={1.0}
    >
      {({scale}, viewportRect) => (
        <SVGContainer width={effectiveLayout.width} height={effectiveLayout.height}>
          {Object.values(effectiveLayout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .filter((group) => group.expanded)
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => {
              const childIds = (groupedAssets[group.id] || []).map((n) => n.id);
              const outlineBounds = getGroupBoundsForRender({
                group,
                draggingGroupId: draggingNodeId,
                childNodeIds: childIds,
                draggedNodePositions,
                nodes: effectiveLayout.nodes,
              });
              return (
                <foreignObject
                  {...outlineBounds}
                  key={`${group.id}-outline`}
                  onDoubleClick={(e) => {
                    zoomToGroup(group.id);
                    e.stopPropagation();
                  }}
                >
                  <GroupOutline minimal={scale < MINIMAL_SCALE} />
                </foreignObject>
              );
            })}

          <AssetEdges
            viewportRect={viewportRect}
            selected={selectedGraphNodes.map((n) => n.id)}
            highlighted={highlighted}
            edges={edgesForRender}
            direction={direction}
            strokeWidth={4}
          />

          {Object.values(effectiveLayout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => {
              const childIds = (groupedAssets[group.id] || []).map((n) => n.id);
              const activeBounds = getGroupBoundsForRender({
                group,
                draggingGroupId: draggingNodeId,
                childNodeIds: childIds,
                draggedNodePositions,
                nodes: effectiveLayout.nodes,
              });
              const groupManualPosition = getGroupManualPositionState(
                overrides,
                group.id,
                childIds,
                group.expanded,
              );
              const onResetGroupPosition = groupManualPosition.isManuallyPositioned
                ? () => resetMultiplePositions(groupManualPosition.resetIds)
                : undefined;

              return group.expanded ? (
                <foreignObject
                  key={group.id}
                  {...activeBounds}
                  className="group"
                  onDoubleClick={(e) => {
                    zoomToGroup(group.id);
                    e.stopPropagation();
                  }}
                >
                  <ExpandedGroupNode
                    setHighlighted={setHighlighted}
                    preferredJobName={explorerPath.pipelineName}
                    onFilterToGroup={() => onFilterToGroup(group)}
                    group={{...group, assets: groupedAssets[group.id] || []}}
                    minimal={scale < MINIMAL_SCALE}
                    onCollapse={() => {
                      focusGroupIdAfterLayoutRef.current = group.id;
                      setExpandedGroups(expandedGroups.filter((g) => g !== group.id));
                    }}
                    isDragging={draggingNodeId === group.id}
                    isManuallyPositioned={groupManualPosition.isManuallyPositioned}
                    onDragStart={(e) => onGroupMouseDown(group.id, childIds, e)}
                    onResetPosition={onResetGroupPosition}
                    toggleSelectAllNodes={(e: React.MouseEvent) => {
                      toggleSelectAllGroupNodesById(e, group.id);
                    }}
                  />
                </foreignObject>
              ) : (
                <foreignObject
                  key={group.id}
                  {...activeBounds}
                  className="group"
                  onMouseEnter={() => setHighlighted([group.id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onDoubleClick={(e) => {
                    if (!viewportEl.current) {
                      return;
                    }
                    const targetScale = viewportEl.current.scaleForSVGBounds(
                      activeBounds.width,
                      activeBounds.height,
                    );
                    viewportEl.current.zoomToSVGBox(activeBounds, true, targetScale * 0.9);
                    e.stopPropagation();
                  }}
                >
                  <CollapsedGroupNode
                    preferredJobName={explorerPath.pipelineName}
                    onFilterToGroup={() => onFilterToGroup(group)}
                    minimal={scale < MINIMAL_SCALE}
                    group={{
                      ...group,
                      assetCount: allGroupCounts[group.id] || 0,
                      assets: groupedAssets[group.id] || [],
                    }}
                    onExpand={() => {
                      focusGroupIdAfterLayoutRef.current = group.id;
                      setExpandedGroups([...expandedGroups, group.id]);
                    }}
                    isDragging={draggingNodeId === group.id}
                    isManuallyPositioned={groupManualPosition.isManuallyPositioned}
                    onDragStart={(e) => onGroupMouseDown(group.id, [], e)}
                    onResetPosition={onResetGroupPosition}
                    toggleSelectAllNodes={(e: React.MouseEvent) => {
                      toggleSelectAllGroupNodesById(e, group.id);
                    }}
                  />
                </foreignObject>
              );
            })}

          {Object.values(effectiveLayout.nodes)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .map(({id, bounds}) => {
              // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
              const graphNode = assetGraphData.nodes[id]!;
              const path = JSON.parse(id);
              if (scale < GROUPS_ONLY_SCALE) {
                return;
              }
              if (bounds.width === 1) {
                return;
              }

              // Apply ephemeral drag position for any node being dragged
              // (single node drag or group drag — all dragged nodes are in draggedNodePositions)
              const dragPos = draggedNodePositions[id];
              const activeBounds = dragPos ? {...bounds, x: dragPos.x, y: dragPos.y} : bounds;

              const contextMenuProps: AssetNodeMenuProps = {
                graphData: fullAssetGraphData,
                node: graphNode,
                explorerPath,
                onChangeExplorerPath,
                selectNode: selectNodeById,
              };
              return (
                <foreignObject
                  {...activeBounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onClick={(e) => onSelectNode(e, {path}, graphNode)}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(activeBounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  {!graphNode ? (
                    <AssetNodeLink assetKey={{path}} />
                  ) : scale < MINIMAL_SCALE || facets.size === 0 ? (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNodeMinimal
                        facets={facets}
                        definition={graphNode.definition}
                        selected={selectedGraphNodes.includes(graphNode)}
                        height={activeBounds.height}
                        isDragging={draggingNodeId === id}
                        isManuallyPositioned={!!overrides[id]}
                        onDragStart={(e) => onNodeMouseDown(id, e)}
                        onResetPosition={overrides[id] ? () => resetNodePosition(id) : undefined}
                      />
                    </AssetNodeContextMenuWrapper>
                  ) : (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNode
                        facets={facets}
                        definition={graphNode.definition}
                        selected={selectedGraphNodes.includes(graphNode)}
                        onChangeAssetSelection={onChangeAssetSelection}
                        isDragging={draggingNodeId === id}
                        isManuallyPositioned={!!overrides[id]}
                        onDragStart={(e) => onNodeMouseDown(id, e)}
                        onResetPosition={overrides[id] ? () => resetNodePosition(id) : undefined}
                      />
                    </AssetNodeContextMenuWrapper>
                  )}
                </foreignObject>
              );
            })}
        </SVGContainer>
      )}
    </SVGViewport>
  ) : null;

  const nextLayoutLoading = layoutLoading || dataLoading;
  const isInitialLayout = useRef(true);
  if (!nextLayoutLoading && isInitialLayout.current) {
    isInitialLayout.current = false;
  }
  const loading = (layoutLoading || dataLoading) && isInitialLayout.current;

  const [errorState, setErrorState] = useState<SyntaxError[]>([]);

  const extraDropdownOptions = useCatalogExtraDropdownOptions(
    useMemo(
      () => ({
        scope: {selected: selectedGraphNodes.map((n) => ({assetKey: n.assetKey}))},
      }),
      [selectedGraphNodes],
    ),
  );

  useFullScreenAllowedView();
  const {isFullScreen, toggleFullScreen} = useFullScreen();

  const toggleFullScreenButton = useMemo(() => {
    return (
      <Tooltip content={isFullScreen ? 'Collapse' : 'Expand'}>
        <Button
          icon={<Icon name={isFullScreen ? 'collapse_fullscreen' : 'expand_fullscreen'} />}
          onClick={toggleFullScreen}
        />
      </Tooltip>
    );
  }, [toggleFullScreen, isFullScreen]);

  const rightPanel = useMemo(() => {
    if (selectedGraphNodes.length === 1 && selectedGraphNodes[0]) {
      return (
        <RightInfoPanel>
          <RightInfoPanelContent>
            <ErrorBoundary region="asset sidebar" resetErrorOnChange={[selectedGraphNodes[0].id]}>
              <SidebarAssetInfo
                graphNode={selectedGraphNodes[0]}
                onToggleCollapse={() => {
                  setRightPanelHidden(true);
                }}
              />
            </ErrorBoundary>
          </RightInfoPanelContent>
        </RightInfoPanel>
      );
    }

    if (fetchOptions.pipelineSelector) {
      return (
        <RightInfoPanel>
          <RightInfoPanelContent>
            <ErrorBoundary region="asset job sidebar">
              <AssetGraphJobSidebar pipelineSelector={fetchOptions.pipelineSelector} />
            </ErrorBoundary>
          </RightInfoPanelContent>
        </RightInfoPanel>
      );
    }

    return null;
  }, [fetchOptions.pipelineSelector, selectedGraphNodes]);

  const renderNotice = () => {
    if (graphQueryItems.length === 0) {
      return <EmptyDAGNotice nodeType="asset" isGraph />;
    }
    if (Object.keys(assetGraphData.nodes).length === 0) {
      if (errorState.length > 0) {
        return <InvalidSelectionQueryNotice errors={errorState} />;
      }
      return <EntirelyFilteredDAGNotice nodeType="asset" />;
    }
    if (error === 'cycles') {
      return <CycleDetectedNotice />;
    }
    if (error === 'too-large') {
      return <LargeDAGNotice nodeType="asset" setForceLargeGraph={setForceLargeGraph} />;
    }
    return null;
  };

  const renderContent = () => {
    if (error) {
      return null;
    }
    if (loading && !layout) {
      return <LoadingNotice async={async} nodeType="asset" />;
    }
    return (
      <AssetGraphBackgroundContextMenu
        direction={direction}
        setDirection={setDirection}
        allGroups={allGroups}
        expandedGroups={expandedGroups}
        setExpandedGroups={setExpandedGroups}
        hideEdgesToNodesOutsideQuery={fetchOptions.hideEdgesToNodesOutsideQuery}
        setHideEdgesToNodesOutsideQuery={setHideEdgesToNodesOutsideQuery}
      >
        {svgViewport}
      </AssetGraphBackgroundContextMenu>
    );
  };

  const explorer = (
    <SplitPanelContainer
      key="explorer"
      identifier="asset-graph-explorer"
      firstInitialPercent={70}
      firstMinSize={400}
      secondMinSize={400}
      first={
        loading ? (
          <LoadingContainer>
            <Box margin={{bottom: 24}}>Loading assets…</Box>
            <Spinner purpose="page" />
          </LoadingContainer>
        ) : (
          <ErrorBoundary region="graph">
            {renderNotice()}
            {renderContent()}
            {setOptions && (
              <OptionsOverlay>
                <Checkbox
                  format="switch"
                  label="View as Asset Graph"
                  checked={options.preferAssetRendering}
                  onChange={() => {
                    onChangeExplorerPath(
                      {...explorerPath, opNames: selectedDefinitions[0]?.opNames || []},
                      'replace',
                    );
                    setOptions({
                      ...options,
                      preferAssetRendering: !options.preferAssetRendering,
                    });
                  }}
                />
              </OptionsOverlay>
            )}

            <TopbarWrapper $isFullScreen={isFullScreen} $viewType={viewType}>
              <Box flex={{direction: 'column'}} style={{width: '100%'}}>
                {isFullScreen ? <IndeterminateLoadingBar $loading={nextLayoutLoading} /> : null}
                <Box
                  flex={{gap: 12, alignItems: 'flex-start'}}
                  padding={{left: showSidebar ? 12 : 24, vertical: 12, right: 12}}
                >
                  {showSidebar ? undefined : (
                    <Tooltip content="Show sidebar">
                      <Button
                        icon={<Icon name="panel_show_left" />}
                        onClick={() => {
                          setShowSidebar(true);
                        }}
                      />
                    </Tooltip>
                  )}
                  {viewType !== AssetGraphViewType.CATALOG && observeEnabled()
                    ? toggleFullScreenButton
                    : null}
                  {viewType === AssetGraphViewType.CATALOG ? (
                    <>
                      {toggleFullScreenButton}
                      <div style={{flex: 1}} />
                    </>
                  ) : (
                    <>
                      <GraphQueryInputFlexWrap>
                        <AssetSelectionInput
                          assets={graphQueryItems}
                          value={explorerPath.opsQuery}
                          onChange={onChangeAssetSelection}
                          onErrorStateChange={(errors: SyntaxError[]) => {
                            if (errors !== errorState) {
                              setErrorState(errors);
                            }
                          }}
                        />
                      </GraphQueryInputFlexWrap>
                      <CreateCatalogViewButton />
                      <AssetLiveDataRefreshButton />
                    </>
                  )}
                  {isIframe() ? null : (
                    <LaunchAssetExecutionButton
                      preferredJobName={explorerPath.pipelineName}
                      scope={
                        nextLayoutLoading
                          ? {all: []}
                          : selectedDefinitions.length
                            ? {selected: selectedDefinitions}
                            : {all: allDefinitionsForMaterialize}
                      }
                      additionalDropdownOptions={extraDropdownOptions}
                    />
                  )}
                </Box>
                {isFullScreen && viewType === AssetGraphViewType.CATALOG ? null : (
                  <IndeterminateLoadingBar
                    $loading={nextLayoutLoading}
                    style={{
                      position: 'absolute',
                      left: 0,
                      right: 0,
                      bottom: -2,
                    }}
                  />
                )}
              </Box>
            </TopbarWrapper>
            {rightPanel && rightPanelHidden ? (
              <RightPanelRevealButton>
                <Tooltip content="Show details panel">
                  <Button
                    icon={<Icon name="panel_show_right" />}
                    title="Show details panel"
                    aria-label="Show details panel"
                    onClick={() => {
                      setRightPanelHidden(false);
                    }}
                  />
                </Tooltip>
              </RightPanelRevealButton>
            ) : null}
          </ErrorBoundary>
        )
      }
      second={(() => {
        if (loading) {
          // If the page is loading but it /will/ show the sidebar when it loads,
          // go ahead and place an empty div so that the drawer doesn't animate out
          // when the page loads. The animation causes "zoom-to-center selected node"
          // to fail because the viewport size is still the full width.
          return selectedTokens.length === 1 ? <div /> : null;
        }
        if (rightPanelHidden) {
          return null;
        }
        return rightPanel;
      })()}
    />
  );

  return (
    <SplitPanelContainer
      key="explorer-wrapper"
      identifier="explorer-wrapper"
      firstMinSize={300}
      firstInitialPercent={0}
      secondMinSize={400}
      first={
        showSidebar ? (
          <AssetGraphExplorerSidebar
            viewType={viewType}
            allAssetKeys={allAssetKeys}
            assetGraphData={assetGraphData}
            fullAssetGraphData={fullAssetGraphData}
            selectedNodes={selectedGraphNodes}
            selectNode={selectNodeById}
            explorerPath={explorerPath}
            onChangeExplorerPath={onChangeExplorerPath}
            hideSidebar={() => {
              setShowSidebar(false);
            }}
            onFilterToGroup={onFilterToGroup}
            loading={loading}
          />
        ) : null
      }
      second={explorer}
    />
  );
};

export interface AssetGroup {
  groupName: string;

  // remove when groups-outside-code-location feature flag is shipped
  repositoryName?: string;
  repositoryLocationName?: string;
}

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;

  foreignObject.group {
    transition: opacity 300ms linear;
  }
`;

const TopbarWrapper = styled.div<{$isFullScreen?: boolean; $viewType: AssetGraphViewType}>`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  ${({$isFullScreen, $viewType}) => {
    return $isFullScreen && $viewType === AssetGraphViewType.CATALOG
      ? ''
      : `
        background: ${Colors.backgroundDefault()};
        border-bottom: 1px solid ${Colors.keylineDefault()};
      `;
  }}
  gap: 12px;
  align-items: center;
`;

const RightPanelRevealButton = styled.div`
  position: absolute;
  top: 88px;
  right: 0;
  z-index: 2;

  button {
    border-top-right-radius: 0;
    border-bottom-right-radius: 0;
    box-shadow: none;
  }
`;

const GraphQueryInputFlexWrap = styled.div`
  flex: 1;

  > div {
    > * {
      display: block;
      width: 100%;
    }
  }
`;

function layoutChangeShouldAdjustViewport(
  last: AssetGraphLayout | null,
  current: AssetGraphLayout,
) {
  if (last === current) {
    return false;
  }
  if (!last) {
    return true;
  }
  return (
    last.edges.length !== current.edges.length ||
    last.nodes.length !== current.nodes.length ||
    Object.keys(last.groups).length !== Object.keys(current.groups).length
  );
}
