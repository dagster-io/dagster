import {
  Box,
  Button,
  Checkbox,
  Colors,
  ErrorBoundary,
  Icon,
  Menu,
  MenuItem,
  NonIdealState,
  SplitPanelContainer,
  TextInputContainer,
  Tooltip,
} from '@dagster-io/ui-components';
import pickBy from 'lodash/pickBy';
import uniq from 'lodash/uniq';
import without from 'lodash/without';
import * as React from 'react';
import {useMemo} from 'react';
import styled from 'styled-components';

import {AssetEdges} from './AssetEdges';
import {useAssetGraphExplorerFilters} from './AssetGraphExplorerFilters';
import {AssetGraphJobSidebar} from './AssetGraphJobSidebar';
import {AssetNode, AssetNodeContextMenuWrapper, AssetNodeMinimal} from './AssetNode';
import {AssetNodeMenuProps} from './AssetNodeMenu';
import {CollapsedGroupNode} from './CollapsedGroupNode';
import {ContextMenuWrapper} from './ContextMenuWrapper';
import {ExpandedGroupNode, GroupOutline} from './ExpandedGroupNode';
import {AssetNodeLink} from './ForeignNode';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  GraphData,
  GraphNode,
  graphHasCycles,
  groupIdForNode,
  isGroupId,
  tokenForAssetKey,
} from './Utils';
import {assetKeyTokensInRange} from './assetKeyTokensInRange';
import {AssetGraphLayout, AssetLayoutDirection, GroupLayout} from './layout';
import {AssetGraphExplorerSidebar} from './sidebar/Sidebar';
import {AssetNodeForGraphQueryFragment} from './types/useAssetGraphData.types';
import {AssetGraphFetchScope, AssetGraphQueryItem, useAssetGraphData} from './useAssetGraphData';
import {AssetLocation, useFindAssetLocation} from './useFindAssetLocation';
import {ShortcutHandler} from '../app/ShortcutHandler';
import {AssetLiveDataRefreshButton} from '../asset-data/AssetLiveDataProvider';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {LaunchAssetObservationButton} from '../assets/LaunchAssetObservationButton';
import {AssetKey} from '../assets/types';
import {DEFAULT_MAX_ZOOM, SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {closestNodeInDirection, isNodeOffscreen} from '../graph/common';
import {AssetGroupSelector, ChangeReason} from '../graphql/types';
import {useQueryAndLocalStoragePersistedState} from '../hooks/useQueryAndLocalStoragePersistedState';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {PageLoadTrace} from '../performance';
import {
  GraphExplorerOptions,
  OptionsOverlay,
  RightInfoPanel,
  RightInfoPanelContent,
} from '../pipelines/GraphExplorer';
import {EmptyDAGNotice, EntirelyFilteredDAGNotice, LoadingNotice} from '../pipelines/GraphNotices';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Loading} from '../ui/Loading';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

type AssetNode = AssetNodeForGraphQueryFragment;

type OptionalFilters =
  | {
      filters: {
        groups?: AssetGroupSelector[];
        computeKindTags?: string[];
        changedInBranch?: ChangeReason[];
      };
      setFilters: React.Dispatch<
        React.SetStateAction<{
          groups?: AssetGroupSelector[];
          computeKindTags?: string[];
          changedInBranch?: ChangeReason[];
        }>
      >;
    }
  | {filters?: null; setFilters?: null};

type Props = {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  fetchOptions: AssetGraphFetchScope;

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToSourceAssetNode: (node: AssetLocation) => void;
  isGlobalGraph?: boolean;
  trace?: PageLoadTrace;
} & OptionalFilters;

export const MINIMAL_SCALE = 0.6;
export const GROUPS_ONLY_SCALE = 0.15;

const emptyArray: any[] = [];

export const AssetGraphExplorer = (props: Props) => {
  const {fetchResult, assetGraphData, fullAssetGraphData, graphQueryItems, allAssetKeys} =
    useAssetGraphData(props.explorerPath.opsQuery, {
      ...props.fetchOptions,
      computeKinds: props.filters?.computeKindTags,
    });

  const {visibleRepos} = React.useContext(WorkspaceContext);

  const assetGroups: AssetGroupSelector[] = React.useMemo(() => {
    return visibleRepos.flatMap((repo) =>
      repo.repository.assetGroups.map((g) => ({
        groupName: g.groupName,
        repositoryLocationName: repo.repositoryLocation.name,
        repositoryName: repo.repository.name,
      })),
    );
  }, [visibleRepos]);

  const {explorerPath, onChangeExplorerPath} = props;

  const {filters, setFilters} = props;

  const setComputeKindTags = React.useCallback(
    (tags: string[]) =>
      setFilters?.({
        ...filters,
        computeKindTags: tags,
      }),
    [setFilters, filters],
  );

  const setGroupFilters = React.useCallback(
    (groups: AssetGroupSelector[]) => setFilters?.({...filters, groups}),
    [filters, setFilters],
  );

  const setChangedInBranch = React.useCallback(
    (changedInBranch: ChangeReason[]) =>
      setFilters?.({
        ...filters,
        changedInBranch,
      }),
    [filters, setFilters],
  );

  const {button, filterBar} = useAssetGraphExplorerFilters({
    nodes: React.useMemo(
      () => (fullAssetGraphData ? Object.values(fullAssetGraphData.nodes) : []),
      [fullAssetGraphData],
    ),
    isGlobalGraph: !!props.isGlobalGraph,
    assetGroups,
    visibleAssetGroups: React.useMemo(() => props.filters?.groups || [], [props.filters?.groups]),
    setGroupFilters: props.filters?.groups ? setGroupFilters : undefined,
    computeKindTags: props.filters?.computeKindTags || emptyArray,
    setComputeKindTags: props.filters?.computeKindTags ? setComputeKindTags : undefined,
    changedInBranch: React.useMemo(
      () => props.filters?.changedInBranch || [],
      [props.filters?.changedInBranch],
    ),
    setChangedInBranch: props.filters?.changedInBranch ? setChangedInBranch : undefined,
    explorerPath: explorerPath.opsQuery,
    clearExplorerPath: React.useCallback(() => {
      onChangeExplorerPath(
        {
          ...explorerPath,
          opsQuery: '',
        },
        'push',
      );
    }, [explorerPath, onChangeExplorerPath]),
  });

  return (
    <Loading allowStaleData queryResult={fetchResult}>
      {() => {
        if (!assetGraphData || !allAssetKeys || !fullAssetGraphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(assetGraphData);

        if (hasCycles) {
          return (
            <NonIdealState
              icon="error"
              title="Cycle detected"
              description="Assets dependencies form a cycle"
            />
          );
        }
        return (
          <AssetGraphExplorerWithData
            key={props.explorerPath.pipelineName}
            assetGraphData={assetGraphData}
            fullAssetGraphData={fullAssetGraphData}
            allAssetKeys={allAssetKeys}
            graphQueryItems={graphQueryItems}
            filterBar={filterBar}
            filterButton={button}
            {...props}
          />
        );
      }}
    </Loading>
  );
};

type WithDataProps = Props & {
  allAssetKeys: AssetKey[];
  assetGraphData: GraphData;
  fullAssetGraphData: GraphData;
  graphQueryItems: AssetGraphQueryItem[];

  filterButton?: React.ReactNode;
  filterBar?: React.ReactNode;
  isGlobalGraph?: boolean;
  trace?: PageLoadTrace;
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
  filterButton,
  filterBar,
  filters,
  setFilters,
  isGlobalGraph = false,
  trace,
}: WithDataProps) => {
  const findAssetLocation = useFindAssetLocation();
  const [highlighted, setHighlighted] = React.useState<string[] | null>(null);

  const {allGroups, allGroupCounts, groupedAssets} = React.useMemo(() => {
    const groupedAssets: Record<string, GraphNode[]> = {};
    Object.values(assetGraphData.nodes).forEach((node) => {
      const groupId = groupIdForNode(node);
      groupedAssets[groupId] = groupedAssets[groupId] || [];
      groupedAssets[groupId]!.push(node);
    });
    const counts: Record<string, number> = {};
    Object.keys(groupedAssets).forEach((key) => (counts[key] = groupedAssets[key]!.length));
    return {allGroups: Object.keys(groupedAssets), allGroupCounts: counts, groupedAssets};
  }, [assetGraphData]);

  const [direction, setDirection] = useStateWithStorage<AssetLayoutDirection>(
    'asset-graph-direction',
    (json) => (['vertical', 'horizontal'].includes(json) ? json : 'horizontal'),
  );
  const [expandedGroups, setExpandedGroups] = useQueryAndLocalStoragePersistedState<string[]>({
    localStorageKey: `asset-graph-open-graph-nodes-${isGlobalGraph}-${explorerPath.pipelineName}`,
    encode: (arr) => ({expanded: arr.length ? arr.join(',') : undefined}),
    decode: (qs) => (qs.expanded || '').split(',').filter(Boolean),
    isEmptyState: (val) => val.length === 0,
  });
  const focusGroupIdAfterLayoutRef = React.useRef('');

  const {layout, loading, async} = useAssetLayout(
    assetGraphData,
    expandedGroups,
    useMemo(() => ({direction}), [direction]),
  );

  React.useEffect(() => {
    if (!loading) {
      trace?.endTrace();
    }
  }, [loading, trace]);

  const viewportEl = React.useRef<SVGViewport>();

  const selectedTokens = explorerPath.opNames[explorerPath.opNames.length - 1]!.split(',');
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedTokens.includes(tokenForAssetKey(node.definition.assetKey)),
  );
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
        return onNavigateToSourceAssetNode(await findAssetLocation(assetKey));
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

        const existing = explorerPath.opNames[0]!.split(',');
        nextOpsNameSelection = (
          existing.includes(token) ? without(existing, token) : uniq([...existing, ...tokensToAdd])
        ).join(',');
      }

      const nextCenter = layout?.nodes[nextOpsNameSelection[nextOpsNameSelection.length - 1]!];
      if (nextCenter) {
        viewportEl.current?.zoomToSVGCoords(nextCenter.bounds.x, nextCenter.bounds.y, true);
      }

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [nextOpsNameSelection],
          opsQuery: nodeIsInDisplayedGraph
            ? explorerPath.opsQuery
            : `${explorerPath.opsQuery},++"${token}"++`,
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
      layout,
    ],
  );

  const zoomToGroup = React.useCallback(
    (groupId: string, animate = true) => {
      if (!viewportEl.current) {
        return;
      }
      const groupBounds = layout && layout.groups[groupId]?.bounds;
      if (groupBounds) {
        const targetScale = viewportEl.current.scaleForSVGBounds(
          groupBounds.width,
          groupBounds.height,
        );
        viewportEl.current.zoomToSVGBox(
          groupBounds,
          animate,
          Math.min(viewportEl.current.state.scale, targetScale * 0.9),
        );
      }
    },
    [viewportEl, layout],
  );

  const [lastRenderedLayout, setLastRenderedLayout] = React.useState<AssetGraphLayout | null>(null);
  const renderingNewLayout = lastRenderedLayout !== layout;

  React.useEffect(() => {
    if (!renderingNewLayout || !layout || !viewportEl.current) {
      return;
    }
    // The first render where we have our layout and viewport, autocenter or
    // focus on the selected node. (If selection was specified in the URL).
    // Don't animate this change.
    if (
      focusGroupIdAfterLayoutRef.current &&
      layout.groups[focusGroupIdAfterLayoutRef.current]?.expanded
    ) {
      zoomToGroup(focusGroupIdAfterLayoutRef.current, false);
      focusGroupIdAfterLayoutRef.current = '';
    } else if (lastSelectedNode) {
      const layoutNode = layout.nodes[lastSelectedNode.id];
      if (layoutNode) {
        viewportEl.current.zoomToSVGBox(layoutNode.bounds, false);
      }
      viewportEl.current.focus();
    } else {
      viewportEl.current.autocenter(false);
    }
    setLastRenderedLayout(layout);
  }, [renderingNewLayout, lastSelectedNode, layout, viewportEl, zoomToGroup]);

  const onClickBackground = () =>
    onChangeExplorerPath(
      {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
      'replace',
    );

  const onArrowKeyDown = (e: React.KeyboardEvent<any>, dir: 'left' | 'right' | 'up' | 'down') => {
    if (!layout || !lastSelectedNode) {
      return;
    }
    const hasDefinition = (node: {id: string}) => !!assetGraphData.nodes[node.id]?.definition;
    const layoutWithoutExternalLinks = {...layout, nodes: pickBy(layout.nodes, hasDefinition)};

    const nextId = closestNodeInDirection(layoutWithoutExternalLinks, lastSelectedNode.id, dir);
    selectNodeById(e, nextId);
  };

  const toggleSelectAllGroupNodesById = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, groupId: string) => {
      const assets = groupedAssets[groupId] || [];
      const childNodeTokens = assets.map((n) => tokenForAssetKey(n.assetKey));

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

  const selectNodeById = React.useCallback(
    (e: React.MouseEvent<any> | React.KeyboardEvent<any>, nodeId?: string) => {
      if (!nodeId) {
        return;
      }
      if (isGroupId(nodeId)) {
        zoomToGroup(nodeId);

        if (e.metaKey) {
          toggleSelectAllGroupNodesById(e, nodeId);
        }

        return;
      }
      const node = assetGraphData.nodes[nodeId];
      if (!node) {
        return;
      }

      onSelectNode(e, node.assetKey, node);

      const nodeBounds = layout && layout.nodes[nodeId]?.bounds;
      if (nodeBounds && viewportEl.current) {
        viewportEl.current.zoomToSVGBox(nodeBounds, true);
      } else {
        setExpandedGroups([...expandedGroups, groupIdForNode(node)]);
      }
    },
    [
      assetGraphData.nodes,
      onSelectNode,
      layout,
      zoomToGroup,
      toggleSelectAllGroupNodesById,
      setExpandedGroups,
      expandedGroups,
    ],
  );

  const [showSidebar, setShowSidebar] = React.useState(isGlobalGraph);

  const onFilterToGroup = (group: AssetGroup | GroupLayout) => {
    setFilters?.({
      ...filters,
      groups: [
        {
          groupName: group.groupName,
          repositoryName: group.repositoryName,
          repositoryLocationName: group.repositoryLocationName,
        },
      ],
    });
  };

  const areAllGroupsCollapsed = expandedGroups.length === 0;
  const areAllGroupsExpanded = expandedGroups.length === allGroups.length;

  const svgViewport = layout ? (
    <SVGViewport
      ref={(r) => (viewportEl.current = r || undefined)}
      defaultZoom="zoom-to-fit-width"
      interactor={SVGViewport.Interactors.PanAndZoom}
      graphWidth={layout.width}
      graphHeight={layout.height}
      graphHasNoMinimumZoom={false}
      additionalToolbarElements={
        <>
          {allGroups.length > 1 && (
            <ToggleGroupsButton
              key="toggle-groups"
              expandedGroups={expandedGroups}
              setExpandedGroups={setExpandedGroups}
              allGroups={allGroups}
            />
          )}
          <ToggleDirectionButton
            key="toggle-direction"
            direction={direction}
            setDirection={setDirection}
          />
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
        <SVGContainer width={layout.width} height={layout.height}>
          {Object.values(layout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .filter((group) => group.expanded)
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) => (
              <foreignObject
                {...group.bounds}
                key={`${group.id}-outline`}
                onDoubleClick={(e) => {
                  zoomToGroup(group.id);
                  e.stopPropagation();
                }}
              >
                <GroupOutline $minimal={scale < MINIMAL_SCALE} />
              </foreignObject>
            ))}

          <AssetEdges
            viewportRect={viewportRect}
            selected={selectedGraphNodes.map((n) => n.id)}
            highlighted={highlighted}
            edges={layout.edges}
            direction={direction}
            strokeWidth={4}
          />

          {Object.values(layout.groups)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .sort((a, b) => a.id.length - b.id.length)
            .map((group) =>
              group.expanded ? (
                <foreignObject
                  key={group.id}
                  {...group.bounds}
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
                    toggleSelectAllNodes={(e: React.MouseEvent) => {
                      toggleSelectAllGroupNodesById(e, group.id);
                    }}
                  />
                </foreignObject>
              ) : (
                <foreignObject
                  key={group.id}
                  {...group.bounds}
                  className="group"
                  onMouseEnter={() => setHighlighted([group.id])}
                  onMouseLeave={() => setHighlighted(null)}
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
                    toggleSelectAllNodes={(e: React.MouseEvent) => {
                      toggleSelectAllGroupNodesById(e, group.id);
                    }}
                  />
                </foreignObject>
              ),
            )}

          {Object.values(layout.nodes)
            .filter((node) => !isNodeOffscreen(node.bounds, viewportRect))
            .map(({id, bounds}) => {
              const graphNode = assetGraphData.nodes[id]!;
              const path = JSON.parse(id);
              if (scale < GROUPS_ONLY_SCALE) {
                return;
              }
              if (bounds.width === 1) {
                return;
              }

              const contextMenuProps: AssetNodeMenuProps = {
                graphData: fullAssetGraphData,
                node: graphNode,
                explorerPath,
                onChangeExplorerPath,
                selectNode: selectNodeById,
              };
              return (
                <foreignObject
                  {...bounds}
                  key={id}
                  style={{overflow: 'visible'}}
                  onMouseEnter={() => setHighlighted([id])}
                  onMouseLeave={() => setHighlighted(null)}
                  onClick={(e) => onSelectNode(e, {path}, graphNode)}
                  onDoubleClick={(e) => {
                    viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                    e.stopPropagation();
                  }}
                >
                  {!graphNode ? (
                    <AssetNodeLink assetKey={{path}} />
                  ) : scale < MINIMAL_SCALE ? (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNodeMinimal
                        definition={graphNode.definition}
                        selected={selectedGraphNodes.includes(graphNode)}
                        height={bounds.height}
                      />
                    </AssetNodeContextMenuWrapper>
                  ) : (
                    <AssetNodeContextMenuWrapper {...contextMenuProps}>
                      <AssetNode
                        definition={graphNode.definition}
                        selected={selectedGraphNodes.includes(graphNode)}
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

  const explorer = (
    <SplitPanelContainer
      key="explorer"
      identifier="asset-graph-explorer"
      firstInitialPercent={70}
      firstMinSize={400}
      first={
        <ErrorBoundary region="graph">
          {graphQueryItems.length === 0 ? (
            <EmptyDAGNotice nodeType="asset" isGraph />
          ) : Object.keys(assetGraphData.nodes).length === 0 ? (
            <EntirelyFilteredDAGNotice nodeType="asset" />
          ) : undefined}
          {loading || !layout ? (
            <LoadingNotice async={async} nodeType="asset" />
          ) : allGroups.length > 1 ? (
            <ContextMenuWrapper
              wrapperOuterStyles={{width: '100%', height: '100%'}}
              wrapperInnerStyles={{width: '100%', height: '100%'}}
              menu={
                <Menu>
                  {areAllGroupsCollapsed ? null : (
                    <MenuItem
                      text={
                        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                          Collapse all groups <KeyboardTag>⌥E</KeyboardTag>
                        </Box>
                      }
                      icon="unfold_less"
                      onClick={() => {
                        setExpandedGroups([]);
                      }}
                    />
                  )}
                  {areAllGroupsExpanded ? null : (
                    <MenuItem
                      text={
                        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                          Expand all groups
                          {areAllGroupsCollapsed ? <KeyboardTag>⌥E</KeyboardTag> : null}
                        </Box>
                      }
                      icon="unfold_more"
                      onClick={() => {
                        setExpandedGroups(allGroups);
                      }}
                    />
                  )}
                  {direction === 'horizontal' ? (
                    <MenuItem
                      text={
                        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                          Vertical orientation <KeyboardTag>⌥O</KeyboardTag>
                        </Box>
                      }
                      icon="graph_vertical"
                      onClick={() => setDirection?.('vertical')}
                    />
                  ) : (
                    <MenuItem
                      text={
                        <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
                          Horizontal orientation <KeyboardTag>⌥O</KeyboardTag>
                        </Box>
                      }
                      icon="graph_horizontal"
                      onClick={() => setDirection?.('horizontal')}
                    />
                  )}
                </Menu>
              }
            >
              {svgViewport}
            </ContextMenuWrapper>
          ) : (
            svgViewport
          )}
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

          <TopbarWrapper>
            <Box flex={{direction: 'column'}} style={{width: '100%'}}>
              <Box
                border={filterBar ? 'bottom' : undefined}
                flex={{gap: 12, alignItems: 'center'}}
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
                <div>{filterButton}</div>
                <GraphQueryInputFlexWrap>
                  <GraphQueryInput
                    type="asset_graph"
                    items={graphQueryItems}
                    value={explorerPath.opsQuery}
                    placeholder="Type an asset subset…"
                    onChange={(opsQuery) =>
                      onChangeExplorerPath({...explorerPath, opsQuery}, 'replace')
                    }
                    popoverPosition="bottom-left"
                  />
                </GraphQueryInputFlexWrap>
                <AssetLiveDataRefreshButton />
                <LaunchAssetObservationButton
                  preferredJobName={explorerPath.pipelineName}
                  scope={
                    selectedDefinitions.length
                      ? {selected: selectedDefinitions.filter((a) => a.isObservable)}
                      : {all: allDefinitionsForMaterialize.filter((a) => a.isObservable)}
                  }
                />
                <LaunchAssetExecutionButton
                  preferredJobName={explorerPath.pipelineName}
                  scope={
                    selectedDefinitions.length
                      ? {selected: selectedDefinitions}
                      : {all: allDefinitionsForMaterialize}
                  }
                />
              </Box>
              {filterBar}
            </Box>
          </TopbarWrapper>
        </ErrorBoundary>
      }
      second={
        selectedGraphNodes.length === 1 && selectedGraphNodes[0] ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <ErrorBoundary region="asset sidebar" resetErrorOnChange={[selectedGraphNodes[0].id]}>
                <SidebarAssetInfo graphNode={selectedGraphNodes[0]} />
              </ErrorBoundary>
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : fetchOptions.pipelineSelector ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <ErrorBoundary region="asset job sidebar">
                <AssetGraphJobSidebar pipelineSelector={fetchOptions.pipelineSelector} />
              </ErrorBoundary>
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : null
      }
    />
  );

  if (showSidebar) {
    return (
      <SplitPanelContainer
        key="explorer-wrapper"
        identifier="explorer-wrapper"
        firstMinSize={300}
        firstInitialPercent={0}
        first={
          showSidebar ? (
            <AssetGraphExplorerSidebar
              isGlobalGraph={isGlobalGraph}
              allAssetKeys={allAssetKeys}
              assetGraphData={assetGraphData}
              fullAssetGraphData={fullAssetGraphData}
              selectedNodes={selectedGraphNodes}
              selectNode={selectNodeById}
              explorerPath={explorerPath}
              onChangeExplorerPath={onChangeExplorerPath}
              expandedGroups={expandedGroups}
              setExpandedGroups={setExpandedGroups}
              hideSidebar={() => {
                setShowSidebar(false);
              }}
              onFilterToGroup={onFilterToGroup}
            />
          ) : null
        }
        second={explorer}
      />
    );
  }
  return explorer;
};

export interface AssetGroup {
  groupName: string;
  repositoryName: string;
  repositoryLocationName: string;
}

interface KeyboardTagProps {
  $withinTooltip?: boolean;
}

const KeyboardTag = styled.div<KeyboardTagProps>`
  ${(props) => {
    return props.$withinTooltip ? `color: ${Colors.accentWhite()}` : `color: ${Colors.textLight()}`;
  }};
  background: ${Colors.backgroundGray()};
  border-radius: 4px;
  padding: 2px 4px;
  margin-left: 6px;
  font-size: 12px;
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;

  foreignObject.group {
    transition: opacity 300ms linear;
  }
`;

const TopbarWrapper = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  background: ${Colors.backgroundDefault()};
  gap: 12px;
  align-items: center;
  border-bottom: 1px solid ${Colors.keylineDefault()};
`;

const GraphQueryInputFlexWrap = styled.div`
  flex: 1;

  > ${Box} {
    ${TextInputContainer} {
      width: 100%;
    }
    > * {
      display: block;
      width: 100%;
    }
  }
`;

const ToggleGroupsButton = ({
  expandedGroups,
  setExpandedGroups,
  allGroups,
}: {
  expandedGroups: string[];
  setExpandedGroups: (v: string[]) => void;
  allGroups: string[];
}) => (
  <ShortcutHandler
    shortcutLabel="⌥E"
    onShortcut={() => setExpandedGroups(expandedGroups.length === 0 ? allGroups : [])}
    shortcutFilter={(e) => e.altKey && e.code === 'KeyE'}
  >
    {expandedGroups.length === 0 ? (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Expand all groups <KeyboardTag $withinTooltip>⌥E</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="unfold_more" />}
          onClick={() => setExpandedGroups(allGroups)}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    ) : (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Collapse all groups <KeyboardTag $withinTooltip>⌥E</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="unfold_less" />}
          onClick={() => setExpandedGroups([])}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    )}
  </ShortcutHandler>
);

const ToggleDirectionButton = ({
  direction,
  setDirection,
}: {
  direction: AssetLayoutDirection;
  setDirection: (d: AssetLayoutDirection) => void;
}) => (
  <ShortcutHandler
    shortcutLabel="⌥O"
    onShortcut={() => setDirection(direction === 'vertical' ? 'horizontal' : 'vertical')}
    shortcutFilter={(e) => e.altKey && e.code === 'KeyO'}
  >
    {direction === 'horizontal' ? (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Change graph to vertical orientation <KeyboardTag $withinTooltip>⌥O</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="graph_vertical" />}
          onClick={() => setDirection('vertical')}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    ) : (
      <Tooltip
        content={
          <Box flex={{direction: 'row', gap: 4, alignItems: 'center'}}>
            Change graph to horizontal orientation <KeyboardTag $withinTooltip>⌥O</KeyboardTag>
          </Box>
        }
      >
        <Button
          icon={<Icon name="graph_horizontal" />}
          onClick={() => setDirection('horizontal')}
          style={{background: Colors.backgroundDefault()}}
        />
      </Tooltip>
    )}
  </ShortcutHandler>
);
