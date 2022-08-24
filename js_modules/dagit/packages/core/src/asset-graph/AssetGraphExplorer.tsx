import {
  Box,
  Checkbox,
  Colors,
  Icon,
  Mono,
  NonIdealState,
  SplitPanelContainer,
} from '@dagster-io/ui';
import pickBy from 'lodash/pickBy';
import uniq from 'lodash/uniq';
import without from 'lodash/without';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {withMiddleTruncation} from '../app/Util';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {closestNodeInDirection} from '../graph/common';
import {
  GraphExplorerOptions,
  OptionsOverlay,
  QueryOverlay,
  RightInfoPanel,
  RightInfoPanelContent,
} from '../pipelines/GraphExplorer';
import {
  EmptyDAGNotice,
  EntirelyFilteredDAGNotice,
  LargeDAGNotice,
  LoadingNotice,
} from '../pipelines/GraphNotices';
import {ExplorerPath} from '../pipelines/PipelinePathUtils';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Loading} from '../ui/Loading';
import {buildRepoPath} from '../workspace/buildRepoAddress';
import {workspacePath} from '../workspace/workspacePath';

import {AssetConnectedEdges} from './AssetEdges';
import {AssetGraphJobSidebar} from './AssetGraphJobSidebar';
import {AssetNode, AssetNodeMinimal} from './AssetNode';
import {ForeignNode} from './ForeignNode';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  GraphData,
  graphHasCycles,
  LiveData,
  GraphNode,
  isSourceAsset,
  tokenForAssetKey,
} from './Utils';
import {AssetGraphLayout} from './layout';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';
import {AssetGraphFetchScope, useAssetGraphData} from './useAssetGraphData';
import {AssetLocation, useFindAssetLocation} from './useFindAssetLocation';
import {useLiveDataForAssetKeys} from './useLiveDataForAssetKeys';

type AssetNode = AssetGraphQuery_assetNodes;

interface Props {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  fetchOptions: AssetGraphFetchScope;
  fetchOptionFilters?: React.ReactNode;

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
  onNavigateToForeignNode: (node: AssetLocation) => void;
}

export const MINIMAL_SCALE = 0.5;

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    allAssetKeys,
    applyingEmptyDefault,
  } = useAssetGraphData(props.explorerPath.opsQuery, props.fetchOptions);

  const {liveResult, liveDataByNode} = useLiveDataForAssetKeys(graphAssetKeys);
  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

  useDidLaunchEvent(liveResult.refetch);

  return (
    <Loading allowStaleData queryResult={fetchResult}>
      {() => {
        if (!assetGraphData || !allAssetKeys) {
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
            allAssetKeys={allAssetKeys}
            graphQueryItems={graphQueryItems}
            applyingEmptyDefault={applyingEmptyDefault}
            liveDataRefreshState={liveDataRefreshState}
            liveDataByNode={liveDataByNode}
            {...props}
          />
        );
      }}
    </Loading>
  );
};

export const AssetGraphExplorerWithData: React.FC<
  {
    allAssetKeys: AssetKey[];
    assetGraphData: GraphData;
    graphQueryItems: GraphQueryItem[];
    liveDataByNode: LiveData;
    liveDataRefreshState: QueryRefreshState;
    applyingEmptyDefault: boolean;
  } & Props
> = (props) => {
  const {
    options,
    setOptions,
    explorerPath,
    onChangeExplorerPath,
    onNavigateToForeignNode,
    liveDataRefreshState,
    liveDataByNode,
    assetGraphData,
    graphQueryItems,
    applyingEmptyDefault,
    fetchOptions,
  } = props;

  const findAssetLocation = useFindAssetLocation();

  const [highlighted, setHighlighted] = React.useState<string | null>(null);

  const selectedAssetValues = explorerPath.opNames[explorerPath.opNames.length - 1].split(',');
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedAssetValues.includes(tokenForAssetKey(node.definition.assetKey)),
  );
  const lastSelectedNode = selectedGraphNodes[selectedGraphNodes.length - 1];

  const {layout, loading, async} = useAssetLayout(assetGraphData);

  const viewportEl = React.useRef<SVGViewport>();

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
        return onNavigateToForeignNode(await findAssetLocation(assetKey));
      }

      // This asset is in a job and we can stay in the job graph explorer!
      // If it's in our current job, allow shift / meta multi-selection.
      let nextOpsNameSelection = token;

      if (e.shiftKey || e.metaKey) {
        let tokensToAdd = [token];
        if (e.shiftKey && lastSelectedNode && node) {
          const tokensInRange = opsInRange({
            graph: assetGraphData,
            from: lastSelectedNode,
            to: node,
          });
          if (tokensInRange.length) {
            tokensToAdd = tokensInRange;
          }
        }

        const existing = explorerPath.opNames[0].split(',');
        nextOpsNameSelection = (existing.includes(token)
          ? without(existing, token)
          : uniq([...existing, ...tokensToAdd])
        ).join(',');
      }

      const nextCenter = layout?.nodes[nextOpsNameSelection[nextOpsNameSelection.length - 1]];
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
      onNavigateToForeignNode,
      findAssetLocation,
      lastSelectedNode,
      assetGraphData,
      layout,
    ],
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
    if (lastSelectedNode) {
      viewportEl.current.zoomToSVGBox(layout.nodes[lastSelectedNode.id].bounds, false);
      viewportEl.current.focus();
    } else {
      viewportEl.current.autocenter(false);
    }
    setLastRenderedLayout(layout);
  }, [renderingNewLayout, lastSelectedNode, layout, viewportEl]);

  const onClickBackground = () =>
    onChangeExplorerPath(
      {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
      'replace',
    );

  const onArrowKeyDown = (e: React.KeyboardEvent<any>, dir: string) => {
    if (!layout) {
      return;
    }
    const hasDefinition = (node: {id: string}) => !!assetGraphData.nodes[node.id]?.definition;
    const layoutWithoutExternalLinks = {...layout, nodes: pickBy(layout.nodes, hasDefinition)};

    const nextId = closestNodeInDirection(layoutWithoutExternalLinks, lastSelectedNode.id, dir);
    const node = nextId && assetGraphData.nodes[nextId];
    if (node && viewportEl.current) {
      onSelectNode(e, node.assetKey, node);
      viewportEl.current.zoomToSVGBox(layout.nodes[nextId].bounds, true);
    }
  };

  return (
    <SplitPanelContainer
      identifier="explorer"
      firstInitialPercent={70}
      firstMinSize={400}
      first={
        <>
          {graphQueryItems.length === 0 ? (
            <EmptyDAGNotice nodeType="asset" isGraph />
          ) : applyingEmptyDefault ? (
            <LargeDAGNotice nodeType="asset" />
          ) : Object.keys(assetGraphData.nodes).length === 0 ? (
            <EntirelyFilteredDAGNotice nodeType="asset" />
          ) : undefined}
          {loading || !layout ? (
            <LoadingNotice async={async} nodeType="asset" />
          ) : (
            <SVGViewport
              ref={(r) => (viewportEl.current = r || undefined)}
              interactor={SVGViewport.Interactors.PanAndZoom}
              graphWidth={layout.width}
              graphHeight={layout.height}
              onClick={onClickBackground}
              onArrowKeyDown={onArrowKeyDown}
              onDoubleClick={(e) => {
                viewportEl.current?.autocenter(true);
                e.stopPropagation();
              }}
              maxZoom={1.2}
              maxAutocenterZoom={1.0}
            >
              {({scale: _scale}) => (
                <SVGContainer width={layout.width} height={layout.height}>
                  <AssetConnectedEdges highlighted={highlighted} edges={layout.edges} />

                  {Object.values(layout.groups)
                    .sort((a, b) => a.id.length - b.id.length)
                    .map(
                      ({
                        id,
                        bounds,
                        groupName,
                        repositoryName,
                        repositoryLocationName,
                        repositoryDisambiguationRequired,
                      }) => (
                        <foreignObject
                          x={bounds.x}
                          y={bounds.y}
                          width={bounds.width}
                          height={bounds.height}
                          key={id}
                        >
                          <Mono
                            style={{
                              opacity: _scale > MINIMAL_SCALE ? (_scale - MINIMAL_SCALE) / 0.2 : 0,
                              fontWeight: 600,
                              display: 'flex',
                              gap: 6,
                            }}
                          >
                            <Icon name="asset_group" size={20} />
                            <Box flex={{direction: 'column'}}>
                              <Link
                                style={{color: Colors.Gray900}}
                                onClick={(e) => e.stopPropagation()}
                                to={workspacePath(
                                  repositoryName,
                                  repositoryLocationName,
                                  `/asset-groups/${groupName}`,
                                )}
                              >
                                {groupName}
                              </Link>
                              {repositoryDisambiguationRequired && (
                                <GroupRepoName>
                                  {withMiddleTruncation(
                                    buildRepoPath(repositoryName, repositoryLocationName),
                                    {maxLength: 45},
                                  )}
                                </GroupRepoName>
                              )}
                            </Box>
                          </Mono>

                          <GroupOutline
                            style={{
                              marginTop: 6,
                              height:
                                bounds.height -
                                (repositoryDisambiguationRequired ? 24 + 18 : 24) -
                                3,
                              border: `${Math.max(2, 2 / _scale)}px dashed ${Colors.Gray300}`,
                              background: `rgba(223, 223, 223, ${
                                0.4 - Math.max(0, _scale - MINIMAL_SCALE) * 0.3
                              })`,
                            }}
                          />
                        </foreignObject>
                      ),
                    )}

                  {Object.values(layout.nodes).map(({id, bounds}) => {
                    const graphNode = assetGraphData.nodes[id];
                    const path = JSON.parse(id);

                    return (
                      <foreignObject
                        {...bounds}
                        key={id}
                        onMouseEnter={() => setHighlighted(id)}
                        onMouseLeave={() => setHighlighted(null)}
                        onClick={(e) => onSelectNode(e, {path}, graphNode)}
                        onDoubleClick={(e) => {
                          viewportEl.current?.zoomToSVGBox(bounds, true, 1.2);
                          e.stopPropagation();
                        }}
                        style={{overflow: 'visible'}}
                      >
                        {!graphNode || !graphNode.definition.opNames.length ? (
                          <ForeignNode assetKey={{path}} />
                        ) : _scale < MINIMAL_SCALE ? (
                          <AssetNodeMinimal
                            definition={graphNode.definition}
                            selected={selectedGraphNodes.includes(graphNode)}
                          />
                        ) : (
                          <AssetNode
                            definition={graphNode.definition}
                            liveData={liveDataByNode[graphNode.id]}
                            selected={selectedGraphNodes.includes(graphNode)}
                          />
                        )}
                      </foreignObject>
                    );
                  })}
                </SVGContainer>
              )}
            </SVGViewport>
          )}
          {setOptions && (
            <OptionsOverlay>
              <Checkbox
                format="switch"
                label="View as Asset Graph"
                checked={options.preferAssetRendering}
                onChange={() => {
                  onChangeExplorerPath(
                    {
                      ...explorerPath,
                      opNames:
                        selectedGraphNodes.length && selectedGraphNodes[0].definition.opNames.length
                          ? selectedGraphNodes[0].definition.opNames
                          : [],
                    },
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

          <Box
            flex={{direction: 'column', alignItems: 'flex-end', gap: 8}}
            style={{position: 'absolute', right: 12, top: 8}}
          >
            <Box flex={{alignItems: 'center', gap: 12}}>
              <QueryRefreshCountdown
                refreshState={liveDataRefreshState}
                dataDescription="materializations"
              />

              <LaunchAssetExecutionButton
                context={selectedGraphNodes.length ? 'selected' : 'all'}
                assetKeys={(selectedGraphNodes.length
                  ? selectedGraphNodes
                  : Object.values(assetGraphData.nodes).filter((a) => !isSourceAsset(a.definition))
                ).map((n) => n.assetKey)}
                preferredJobName={explorerPath.pipelineName}
              />
            </Box>
          </Box>
          <QueryOverlay>
            {props.fetchOptionFilters}

            <GraphQueryInput
              items={graphQueryItems}
              value={explorerPath.opsQuery}
              placeholder="Type an asset subset…"
              onChange={(opsQuery) => onChangeExplorerPath({...explorerPath, opsQuery}, 'replace')}
              popoverPosition="bottom-left"
            />
          </QueryOverlay>
        </>
      }
      second={
        selectedGraphNodes.length === 1 && selectedGraphNodes[0] ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <SidebarAssetInfo
                assetKey={selectedGraphNodes[0].assetKey}
                liveData={liveDataByNode[selectedGraphNodes[0].id]}
              />
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : fetchOptions.pipelineSelector ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <AssetGraphJobSidebar pipelineSelector={fetchOptions.pipelineSelector} />
            </RightInfoPanelContent>
          </RightInfoPanel>
        ) : null
      }
    />
  );
};

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;

const GroupOutline = styled.div`
  width: 100%;
  border-radius: 10px;
  pointer-events: none;
`;

const GroupRepoName = styled.div`
  font-size: 0.8rem;
  line-height: 0.7rem;
  white-space: nowrap;
  margin-bottom: 4px;
`;

// Helpers

const graphDirectionOf = ({
  graph,
  from,
  to,
}: {
  graph: GraphData;
  from: GraphNode;
  to: GraphNode;
}) => {
  const stack = [from];
  while (stack.length) {
    const node = stack.pop()!;

    const downstream = [...Object.keys(graph.downstream[node.id] || {})]
      .map((n) => graph.nodes[n])
      .filter(Boolean);
    if (downstream.some((d) => d.id === to.id)) {
      return 'downstream';
    }
    stack.push(...downstream);
  }
  return 'upstream';
};

const opsInRange = (
  {graph, from, to}: {graph: GraphData; from: GraphNode; to: GraphNode},
  seen: string[] = [],
) => {
  if (!from) {
    return [];
  }
  if (from.id === to.id) {
    return [...to.definition.opNames];
  }

  if (seen.length === 0 && graphDirectionOf({graph, from, to}) === 'upstream') {
    [from, to] = [to, from];
  }

  const downstream = [...Object.keys(graph.downstream[from.id] || {})]
    .map((n) => graph.nodes[n])
    .filter(Boolean);

  const ledToTarget: string[] = [];

  for (const node of downstream) {
    if (seen.includes(node.id)) {
      continue;
    }
    const result: string[] = opsInRange({graph, from: node, to}, [...seen, from.id]);
    if (result.length) {
      ledToTarget.push(...from.definition.opNames, ...result);
    }
  }
  return uniq(ledToTarget);
};
