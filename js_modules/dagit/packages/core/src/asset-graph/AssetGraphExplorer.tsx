import {Box, Checkbox, NonIdealState, SplitPanelContainer} from '@dagster-io/ui';
import _, {flatMap, uniq, uniqBy, without} from 'lodash';
import React from 'react';
import styled from 'styled-components/macro';

import {GraphQueryItem} from '../app/GraphQueryImpl';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  QueryRefreshState,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {LaunchAssetExecutionButton} from '../assets/LaunchAssetExecutionButton';
import {AssetKey} from '../assets/types';
import {SVGViewport} from '../graph/SVGViewport';
import {useAssetLayout} from '../graph/asyncGraphLayout';
import {closestNodeInDirection, isNodeOffscreen} from '../graph/common';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
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
import {SidebarPipelineOrJobOverview} from '../pipelines/SidebarPipelineOrJobOverview';
import {GraphExplorerSolidHandleFragment} from '../pipelines/types/GraphExplorerSolidHandleFragment';
import {useDidLaunchEvent} from '../runs/RunUtils';
import {PipelineSelector} from '../types/globalTypes';
import {GraphQueryInput} from '../ui/GraphQueryInput';
import {Loading} from '../ui/Loading';

import {AssetEdges} from './AssetEdges';
import {AssetNode} from './AssetNode';
import {ForeignNode} from './ForeignNode';
import {OmittedAssetsNotice} from './OmittedAssetsNotice';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  GraphData,
  graphHasCycles,
  LiveData,
  GraphNode,
  isSourceAsset,
  tokenForAssetKey,
} from './Utils';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';
import {useAssetGraphData} from './useAssetGraphData';
import {useFindAssetInWorkspace} from './useFindAssetInWorkspace';
import {useLiveDataForAssetKeys} from './useLiveDataForAssetKeys';

type AssetNode = AssetGraphQuery_assetNodes;

interface Props {
  options: GraphExplorerOptions;
  setOptions?: (options: GraphExplorerOptions) => void;

  pipelineSelector?: PipelineSelector;
  filterNodes?: (assetNode: AssetGraphQuery_assetNodes) => boolean;

  // Optionally pass op handles to display op metadata on the assets linked to each op.
  // (eg: the "ipynb" tag annotation). Right now, we already have this data loaded for
  // individual jobs, and the global asset graph quietly doesn't display these.
  handles?: GraphExplorerSolidHandleFragment[];

  explorerPath: ExplorerPath;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {
    fetchResult,
    assetGraphData,
    graphQueryItems,
    graphAssetKeys,
    applyingEmptyDefault,
  } = useAssetGraphData(props.pipelineSelector, props.explorerPath.opsQuery, props.filterNodes);

  const {liveResult, liveDataByNode} = useLiveDataForAssetKeys(
    props.pipelineSelector,
    assetGraphData,
    graphAssetKeys,
  );

  const liveDataRefreshState = useQueryRefreshAtInterval(liveResult, FIFTEEN_SECONDS);

  useDocumentTitle('Assets');
  useDidLaunchEvent(liveResult.refetch);

  return (
    <Loading allowStaleData queryResult={fetchResult}>
      {() => {
        if (!assetGraphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const hasCycles = graphHasCycles(assetGraphData);
        const assetKeys = fetchResult.data?.assetNodes.map((a) => a.assetKey) || [];

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
            assetKeys={assetKeys}
            assetGraphData={assetGraphData}
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

const AssetGraphExplorerWithData: React.FC<
  {
    assetKeys: AssetKey[];
    assetGraphData: GraphData;
    graphQueryItems: GraphQueryItem[];
    liveDataByNode: LiveData;
    liveDataRefreshState: QueryRefreshState;
    applyingEmptyDefault: boolean;
  } & Props
> = (props) => {
  const {
    handles = [],
    options,
    setOptions,
    explorerPath,
    onChangeExplorerPath,
    liveDataRefreshState,
    liveDataByNode,
    assetGraphData,
    graphQueryItems,
    applyingEmptyDefault,
    pipelineSelector,
  } = props;

  const findAssetInWorkspace = useFindAssetInWorkspace();

  const selectedAssetValues = explorerPath.opNames[explorerPath.opNames.length - 1].split(',');
  const selectedGraphNodes = Object.values(assetGraphData.nodes).filter((node) =>
    selectedAssetValues.includes(tokenForAssetKey(node.definition.assetKey)),
  );
  const lastSelectedNode = selectedGraphNodes[selectedGraphNodes.length - 1];
  const launchGraphNodes = selectedGraphNodes.length
    ? selectedGraphNodes
    : Object.values(assetGraphData.nodes).filter((a) => !isSourceAsset(a.definition));

  const onSelectNode = React.useCallback(
    async (
      e: React.MouseEvent<any> | React.KeyboardEvent<any>,
      assetKey: {path: string[]},
      node: GraphNode | null,
    ) => {
      e.stopPropagation();

      const token = tokenForAssetKey(assetKey);
      let clicked: {opName: string | null; jobName: string | null} = {opName: null, jobName: null};

      if (node?.definition) {
        // The asset's defintion was provided in our job.assetNodes query. Show it in the current graph.
        clicked = {opName: node.definition.opName, jobName: explorerPath.pipelineName};
      } else {
        // The asset's definition was not provided in our query for job.assetNodes. This means
        // it's in another job or is a source asset not defined in the repository at all.
        clicked = await findAssetInWorkspace(assetKey);
      }

      let nextOpsQuery = explorerPath.opsQuery;
      let nextOpsNameSelection = token;

      // If no opName, this is a source asset.
      if (clicked.jobName !== explorerPath.pipelineName || !clicked.opName) {
        nextOpsQuery = '';
      } else if (e.shiftKey || e.metaKey) {
        const existing = explorerPath.opNames[0].split(',');
        const added =
          e.shiftKey && lastSelectedNode && node
            ? opsInRange({graph: assetGraphData, from: lastSelectedNode, to: node})
            : [token];

        nextOpsNameSelection = (existing.includes(token)
          ? without(existing, token)
          : uniq([...existing, ...added])
        ).join(',');
      }

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [nextOpsNameSelection],
          opsQuery: nextOpsQuery,
          pipelineName: clicked.jobName || explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [explorerPath, onChangeExplorerPath, findAssetInWorkspace, lastSelectedNode, assetGraphData],
  );

  const {layout, loading, async} = useAssetLayout(assetGraphData);

  const viewportEl = React.useRef<SVGViewport>();
  React.useEffect(() => {
    viewportEl.current?.autocenter();
  }, [layout, viewportEl]);

  const onClickBackground = () =>
    onChangeExplorerPath(
      {...explorerPath, pipelineName: explorerPath.pipelineName, opNames: []},
      'replace',
    );

  const onArrowKeyDown = (e: React.KeyboardEvent<any>, dir: string) => {
    const nextId = layout && closestNodeInDirection(layout, lastSelectedNode.id, dir);
    const node = nextId && assetGraphData.nodes[nextId];
    if (node && viewportEl.current) {
      onSelectNode(e, node.assetKey, node);
      viewportEl.current.smoothZoomToSVGBox(layout.nodes[nextId].bounds);
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
              {({scale: _scale}, viewportRect) => (
                <SVGContainer width={layout.width} height={layout.height}>
                  <AssetEdges edges={layout.edges} />

                  {Object.values(layout.nodes).map(({id, bounds}, index) => {
                    const graphNode = assetGraphData.nodes[id];
                    const path = JSON.parse(id);

                    if (isNodeOffscreen(bounds, viewportRect)) {
                      return id === lastSelectedNode?.id ? (
                        <RecenterGraph
                          key={index}
                          viewportRef={viewportEl}
                          x={bounds.x + bounds.width / 2}
                          y={bounds.y + bounds.height / 2}
                        />
                      ) : null;
                    }

                    return (
                      <foreignObject
                        {...bounds}
                        key={id}
                        onClick={(e) => onSelectNode(e, {path}, graphNode)}
                        onDoubleClick={(e) => {
                          viewportEl.current?.smoothZoomToSVGBox(bounds, 1.2);
                          e.stopPropagation();
                        }}
                        style={{overflow: 'visible'}}
                      >
                        {!graphNode || !graphNode.definition.opName ? (
                          <ForeignNode assetKey={{path}} />
                        ) : (
                          <AssetNode
                            definition={graphNode.definition}
                            liveData={liveDataByNode[graphNode.id]}
                            metadata={
                              handles.find((h) => h.handleID === graphNode.definition.opName)?.solid
                                .definition.metadata || []
                            }
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
                        selectedGraphNodes.length && selectedGraphNodes[0].definition.opName
                          ? [selectedGraphNodes[0].definition.opName]
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
            style={{position: 'absolute', right: 12, top: 12}}
          >
            <Box flex={{alignItems: 'center', gap: 12}}>
              <QueryRefreshCountdown refreshState={liveDataRefreshState} />

              <LaunchAssetExecutionButton
                title={titleForLaunch(selectedGraphNodes, liveDataByNode)}
                preferredJobName={explorerPath.pipelineName}
                assets={launchGraphNodes.map((n) => n.definition)}
                upstreamAssetKeys={uniqBy(
                  flatMap(launchGraphNodes.map((n) => n.definition.dependencyKeys)),
                  (key) => JSON.stringify(key),
                ).filter(
                  (key) =>
                    !launchGraphNodes.some(
                      (n) => JSON.stringify(n.assetKey) === JSON.stringify(key),
                    ),
                )}
              />
            </Box>
            {!props.pipelineSelector && <OmittedAssetsNotice assetKeys={props.assetKeys} />}
          </Box>
          <QueryOverlay>
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
        ) : pipelineSelector ? (
          <RightInfoPanel>
            <RightInfoPanelContent>
              <SidebarPipelineOrJobOverview pipelineSelector={pipelineSelector} />
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
    return [to.definition.opName!];
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
      ledToTarget.push(from.definition.opName!, ...result);
    }
  }
  return uniq(ledToTarget);
};

const titleForLaunch = (nodes: GraphNode[], liveDataByNode: LiveData) => {
  const isRematerializeForAll = (nodes.length
    ? nodes.map((n) => liveDataByNode[n.id])
    : Object.values(liveDataByNode)
  ).every((e) => !!e?.lastMaterialization);

  return `${isRematerializeForAll ? 'Rematerialize' : 'Materialize'} ${
    nodes.length === 0 ? `All` : nodes.length === 1 ? `Selected` : `Selected (${nodes.length})`
  }`;
};

// This is similar to react-router's "<Redirect />" in that it immediately performs
// the action you rendered.
//
const RecenterGraph: React.FC<{
  viewportRef: React.MutableRefObject<SVGViewport | undefined>;
  x: number;
  y: number;
}> = ({viewportRef, x, y}) => {
  React.useEffect(() => {
    viewportRef.current?.smoothZoomToSVGCoords(x, y, viewportRef.current.state.scale);
  }, [viewportRef, x, y]);

  return <span />;
};
