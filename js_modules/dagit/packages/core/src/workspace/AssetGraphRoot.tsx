import {gql, useQuery, useMutation} from '@apollo/client';
import {Menu, MenuItem, Colors, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import {ContextMenu2 as ContextMenu} from '@blueprintjs/popover2';
import {pathVerticalDiagonal} from '@vx/shape';
import * as dagre from 'dagre';
import qs from 'query-string';
import React from 'react';
import {useHistory, useRouteMatch, Link, RouteComponentProps} from 'react-router-dom';
import styled, {CSSProperties} from 'styled-components/macro';

import {AppContext} from '../app/AppContext';
import {AssetDetails} from '../assets/AssetDetails';
import {AssetMaterializations} from '../assets/AssetMaterializations';
import {showLaunchError} from '../execute/showLaunchError';
import {SVGViewport} from '../graph/SVGViewport';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {JobMetadata} from '../nav/JobMetadata';
import {Description} from '../pipelines/Description';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {
  LAUNCH_PIPELINE_EXECUTION_MUTATION,
  handleLaunchResult,
  titleForRun,
} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';
import {LaunchPipelineExecution} from '../runs/types/LaunchPipelineExecution';
import {POLL_INTERVAL} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {Box} from '../ui/Box';
import {Loading} from '../ui/Loading';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';
import {FontFamily} from '../ui/styles';

import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  AssetGraphQuery_repositoryOrError_Repository,
  AssetGraphQuery_repositoryOrError_Repository_assetNodes,
  AssetGraphQuery_repositoryOrError_Repository_assetNodes_assetKey,
} from './types/AssetGraphQuery';
import {workspacePath} from './workspacePath';

type Repository = AssetGraphQuery_repositoryOrError_Repository;
type AssetNode = AssetGraphQuery_repositoryOrError_Repository_assetNodes;
type AssetKey = AssetGraphQuery_repositoryOrError_Repository_assetNodes_assetKey;

interface Props extends RouteComponentProps {
  repoAddress: RepoAddress;
  selected: string | undefined;
}

interface Node {
  id: string;
  assetKey: AssetKey;
  definition: AssetNode;
  hidden: boolean;
}
interface LayoutNode {
  id: string;
  x: number;
  y: number;
}
interface GraphData {
  nodes: {[id: string]: Node};
  downstream: {[upstream: string]: {[downstream: string]: string}};
  upstream: {[downstream: string]: {[upstream: string]: boolean}};
}
interface IPoint {
  x: number;
  y: number;
}
type IEdge = {
  from: IPoint;
  to: IPoint;
  dashed: boolean;
};

const getNodeDimensions = (def: AssetNode) => {
  let height = 40;
  if (def.description) {
    height += 25;
  }
  if (def.assetMaterializations.length) {
    height += 22;
    if (runForDisplay(def)) {
      height += 22;
    }
  }
  return {width: Math.max(250, def.assetKey.path.join('>').length * 9.5) + 25, height};
};

const getBlankDimensions = (id: string) => {
  const path = JSON.parse(id);
  return {width: Math.max(250, path.join('>').length * 1.2) + 25, height: 30};
};

const buildGraphData = (repository: Repository, selected?: Node) => {
  const nodes: {[id: string]: Node} = {};
  const downstream: {[downstreamId: string]: {[upstreamId: string]: string}} = {};
  const upstream: {[upstreamId: string]: {[downstreamId: string]: boolean}} = {};

  repository.assetNodes.forEach((definition: AssetNode) => {
    const assetKeyJson = JSON.stringify(definition.assetKey.path);
    definition.dependencies.forEach((dependency) => {
      const upstreamAssetKeyJson = JSON.stringify(dependency.upstreamAsset.assetKey.path);
      downstream[upstreamAssetKeyJson] = {
        ...(downstream[upstreamAssetKeyJson] || {}),
        [assetKeyJson]: dependency.inputName,
      };
      upstream[assetKeyJson] = {
        ...(upstream[assetKeyJson] || {}),
        [upstreamAssetKeyJson]: true,
      };
    });
    nodes[assetKeyJson] = {
      id: assetKeyJson,
      assetKey: definition.assetKey,
      definition,
      hidden: !!selected && definition.jobName !== selected.definition.jobName,
    };
  });

  return {nodes, downstream, upstream};
};

const graphHasCycles = (graphData: GraphData) => {
  const nodes = new Set(Object.keys(graphData.nodes));
  const search = (stack: string[], node: string): boolean => {
    if (stack.indexOf(node) !== -1) {
      return true;
    }
    if (nodes.delete(node) === true) {
      const nextStack = stack.concat(node);
      return Object.keys(graphData.downstream[node] || {}).some((nextNode) =>
        search(nextStack, nextNode),
      );
    }
    return false;
  };
  let hasCycles = false;
  while (nodes.size !== 0) {
    hasCycles = hasCycles || search([], nodes.values().next().value);
  }
  return hasCycles;
};

const layoutGraph = (graphData: GraphData) => {
  const g = new dagre.graphlib.Graph();
  const marginBase = 100;
  const marginy = marginBase;
  const marginx = marginBase;
  g.setGraph({rankdir: 'TB', marginx, marginy});
  g.setDefaultEdgeLabel(() => ({}));

  Object.values(graphData.nodes)
    .filter((x) => !x.hidden)
    .forEach((node) => {
      g.setNode(node.id, getNodeDimensions(node.definition));
    });
  const foreignNodes = {};
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);
    downstreamIds.forEach((downstreamId) => {
      if (graphData.nodes[downstreamId].hidden && graphData.nodes[upstreamId].hidden) {
        return;
      }
      g.setEdge({v: upstreamId, w: downstreamId}, {weight: 1});
      if (graphData.nodes[downstreamId].hidden) {
        foreignNodes[downstreamId] = true;
      } else if (graphData.nodes[upstreamId].hidden) {
        foreignNodes[upstreamId] = true;
      }
    });
  });

  Object.keys(foreignNodes).forEach((upstreamId) => {
    g.setNode(upstreamId, getBlankDimensions(upstreamId));
  });

  dagre.layout(g);

  const dagreNodesById: {[id: string]: dagre.Node} = {};
  g.nodes().forEach((id) => {
    const node = g.node(id);
    if (!node) {
      return;
    }
    dagreNodesById[id] = node;
  });

  let maxWidth = 0;
  let maxHeight = 0;
  const nodes: LayoutNode[] = [];
  Object.keys(dagreNodesById).forEach((id) => {
    const dagreNode = dagreNodesById[id];
    nodes.push({
      id,
      x: dagreNode.x - dagreNode.width / 2,
      y: dagreNode.y - dagreNode.height / 2,
    });
    maxWidth = Math.max(maxWidth, dagreNode.x + dagreNode.width);
    maxHeight = Math.max(maxHeight, dagreNode.y + dagreNode.height);
  });

  const edges: IEdge[] = [];
  g.edges().forEach((e) => {
    const points = g.edge(e).points;
    edges.push({
      from: points[0],
      to: points[points.length - 1],
      dashed: false,
    });
  });

  return {
    nodes,
    edges,
    width: maxWidth,
    height: maxHeight + marginBase,
  };
};

const buildSVGPath = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});

export const AssetGraphRoot: React.FC<Props> = (props) => {
  const {repoAddress, selected} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery(ASSETS_GRAPH_QUERY, {
    variables: {repositorySelector},
    notifyOnNetworkStatusChange: true,
    pollInterval: POLL_INTERVAL,
  });
  const [nodeSelection, setSelectedNode] = React.useState<Node | undefined>();
  const history = useHistory();
  const match = useRouteMatch<{repoPath: string}>();
  React.useEffect(() => {
    if (!selected || !queryResult.data || !queryResult.data.repositoryOrError) {
      return;
    }
    if (queryResult.data.repositoryOrError.__typename !== 'Repository') {
      return;
    }
    const repository = queryResult.data.repositoryOrError;
    repository.assetNodes.forEach((definition: AssetNode) => {
      if (definition.id === selected) {
        setSelectedNode({
          id: JSON.stringify(definition.assetKey.path),
          assetKey: definition.assetKey,
          definition,
          hidden: false,
        });
      }
    });
  }, [selected, queryResult]);

  const selectNode = (node: Node) => {
    if (!node) {
      return;
    }
    setSelectedNode(node);
    history.push(
      `/workspace/${match.params.repoPath}/assets/${node.assetKey.path
        .map(encodeURIComponent)
        .join('/')}`,
    );
  };

  useDocumentTitle('Assets');

  return (
    <Loading allowStaleData queryResult={queryResult}>
      {({repositoryOrError}) => {
        if (repositoryOrError.__typename !== 'Repository') {
          return (
            <NonIdealState
              icon={IconNames.ERROR}
              title="Query Error"
              description={repositoryOrError.message}
            />
          );
        }
        const graphData = buildGraphData(repositoryOrError, nodeSelection);
        const hasCycles = graphHasCycles(graphData);

        if (hasCycles) {
          return (
            <NonIdealState title="Cycle detected" description="Assets dependencies form a cycle" />
          );
        }

        const layout = layoutGraph(graphData);
        const computeStatuses = buildGraphComputeStatuses(graphData);

        const nodeSelectionPipeline =
          nodeSelection && runForDisplay(nodeSelection.definition)?.pipelineName;
        const samePipelineNodes = nodeSelectionPipeline
          ? Object.values(graphData.nodes).filter(
              (n) => runForDisplay(n.definition)?.pipelineName === nodeSelectionPipeline,
            )
          : [];

        if (!Object.keys(graphData.nodes).length) {
          return (
            <NonIdealState
              title="No assets defined"
              description="No assets defined using the @asset definition"
            />
          );
        }

        return (
          <SplitPanelContainer
            identifier="assets"
            firstInitialPercent={70}
            firstMinSize={600}
            first={
              <SVGViewport
                interactor={SVGViewport.Interactors.PanAndZoom}
                graphWidth={layout.width}
                graphHeight={layout.height}
                onKeyDown={() => {}}
                onDoubleClick={() => {}}
                maxZoom={1.2}
                maxAutocenterZoom={1.0}
              >
                {({scale: _scale}: any) => (
                  <SVGContainer width={layout.width} height={layout.height}>
                    <defs>
                      <marker
                        id="arrow"
                        viewBox="0 0 10 10"
                        refX="1"
                        refY="5"
                        markerUnits="strokeWidth"
                        markerWidth="2"
                        markerHeight="4"
                        orient="auto"
                      >
                        <path d="M 0 0 L 10 5 L 0 10 z" fill={Colors.LIGHT_GRAY1} />
                      </marker>
                    </defs>
                    <g opacity={0.8}>
                      {layout.edges.map((edge, idx) => (
                        <StyledPath
                          key={idx}
                          d={buildSVGPath({source: edge.from, target: edge.to})}
                          dashed={edge.dashed}
                          markerEnd="url(#arrow)"
                        />
                      ))}
                    </g>
                    {layout.nodes.map((layoutNode) => {
                      const graphNode = graphData.nodes[layoutNode.id];
                      const {width, height} = graphNode.hidden
                        ? getBlankDimensions(layoutNode.id)
                        : getNodeDimensions(graphNode.definition);
                      return (
                        <foreignObject
                          key={layoutNode.id}
                          x={layoutNode.x}
                          y={layoutNode.y}
                          width={width}
                          height={height}
                          onClick={() => selectNode(graphNode)}
                        >
                          {graphNode.hidden ? (
                            <ForeignNode assetKeyPath={JSON.parse(layoutNode.id)} />
                          ) : (
                            <AssetNode
                              definition={graphNode.definition}
                              selected={nodeSelection?.id === graphNode.id}
                              secondaryHighlight={samePipelineNodes.includes(graphNode)}
                              computeStatus={computeStatuses[graphNode.id]}
                              repoAddress={repoAddress}
                            />
                          )}
                        </foreignObject>
                      );
                    })}
                  </SVGContainer>
                )}
              </SVGViewport>
            }
            second={
              nodeSelection ? (
                <AssetPanel node={nodeSelection} repoAddress={repoAddress} />
              ) : (
                <NonIdealState
                  title="No asset selected"
                  description="Select an asset to see its definition and ops."
                />
              )
            }
          />
        );
      }}
    </Loading>
  );
};

const AssetPanel = ({node, repoAddress}: {node: Node; repoAddress: RepoAddress}) => {
  return (
    <div style={{overflowY: 'auto'}}>
      <Box margin={32} style={{fontWeight: 'bold', fontSize: 18}}>
        {node.assetKey.path.join(' > ')}
      </Box>
      <SidebarSection title="Definition">
        <Box margin={12}>
          <Description description={node.definition.description || null} />
        </Box>
      </SidebarSection>
      <SidebarSection title="Job">
        {node.definition.jobName ? (
          <Box margin={12}>
            <Box margin={{bottom: 8}}>
              <Link
                to={workspacePath(
                  repoAddress.name,
                  repoAddress.location,
                  `/jobs/${node.definition.jobName}`,
                )}
              >
                {node.definition.jobName}
              </Link>
            </Box>
            <JobMetadata
              repoAddress={repoAddress}
              pipelineMode="default"
              pipelineName={node.definition.jobName}
            />
          </Box>
        ) : null}
      </SidebarSection>
      <SidebarSection title={'Latest Materialization'}>
        <Box margin={12}>
          {node.definition.assetMaterializations.length ? (
            <AssetDetails assetKey={node.assetKey} asOf={null} asSidebarSection />
          ) : (
            <div>&mdash;</div>
          )}
        </Box>
      </SidebarSection>

      {node.definition.assetMaterializations.length ? (
        <SidebarSection title={'Plots'}>
          <Box margin={12}>
            <AssetMaterializations assetKey={node.assetKey} asOf={null} asSidebarSection />
          </Box>
        </SidebarSection>
      ) : null}
    </div>
  );
};

function runForDisplay(d: AssetNode) {
  const run = d.assetMaterializations[0]?.runOrError;
  return run && run.__typename === 'PipelineRun' ? run : null;
}

const ASSETS_GRAPH_QUERY = gql`
  query AssetGraphQuery($repositorySelector: RepositorySelector!) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      ... on Repository {
        id
        name
        location {
          id
          name
        }
        assetNodes {
          id
          assetKey {
            path
          }
          opName
          description
          jobName
          dependencies {
            inputName
            upstreamAsset {
              id
              assetKey {
                path
              }
            }
          }
          assetMaterializations(limit: 1) {
            materializationEvent {
              materialization {
                metadataEntries {
                  ...MetadataEntryFragment
                }
              }
              stepStats {
                stepKey
                startTime
                endTime
              }
            }
            runOrError {
              ... on PipelineRun {
                id
                runId
                status
                pipelineName
                mode
              }
            }
          }
        }
        pipelines {
          id
          name
          modes {
            id
            name
          }
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
const StyledPath = styled('path')<{dashed: boolean}>`
  stroke-width: 4;
  stroke: ${Colors.LIGHT_GRAY1};
  ${({dashed}) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;

const ForeignNode: React.FC<{assetKeyPath: string[]}> = ({assetKeyPath}) => (
  <div
    style={{
      border: '1px dashed #aaaaaa',
      background: 'white',
      inset: 0,
    }}
  >
    <div
      style={{
        display: 'flex',
        padding: '4px 8px 6px',
        fontFamily: FontFamily.monospace,
        fontWeight: 600,
      }}
    >
      {assetKeyPath.join(' > ')}
    </div>
  </div>
);

const AssetNode: React.FC<{
  definition: AssetNode;
  selected: boolean;
  computeStatus: Status;
  repoAddress: RepoAddress;
  secondaryHighlight: boolean;
}> = ({definition, selected, computeStatus, repoAddress, secondaryHighlight}) => {
  const [launchPipelineExecution] = useMutation<LaunchPipelineExecution>(
    LAUNCH_PIPELINE_EXECUTION_MUTATION,
  );
  const {basePath} = React.useContext(AppContext);
  const {materializationEvent: event, runOrError} = definition.assetMaterializations[0] || {};

  const onLaunch = async () => {
    if (!definition.jobName) {
      return;
    }

    try {
      const result = await launchPipelineExecution({
        variables: {
          executionParams: {
            selector: {
              pipelineName: definition.jobName,
              ...repoAddressToSelector(repoAddress),
            },
            mode: 'default',
            stepKeys: [definition.opName],
          },
        },
      });
      handleLaunchResult(basePath, definition.jobName, result, true);
    } catch (error) {
      showLaunchError(error as Error);
    }
  };
  return (
    <ContextMenu
      content={
        <Menu>
          <MenuItem
            text={
              <span>
                Launch run to build{' '}
                <span style={{fontFamily: 'monospace', fontWeight: 600}}>
                  {definition.assetKey.path.join(' > ')}
                </span>
              </span>
            }
            icon="send-to"
            onClick={onLaunch}
          />
        </Menu>
      }
    >
      <div
        style={{
          border: '1px solid #ececec',
          outline: selected
            ? `2px solid ${Colors.BLUE4}`
            : secondaryHighlight
            ? `2px solid ${Colors.BLUE4}55`
            : 'none',
          marginTop: 10,
          marginRight: 4,
          marginLeft: 4,
          marginBottom: 2,
          position: 'absolute',
          background: 'white',
          inset: 0,
        }}
      >
        <div
          style={{
            display: 'flex',
            padding: '4px 8px',
            fontFamily: FontFamily.monospace,
            fontWeight: 600,
          }}
        >
          {definition.assetKey.path.join(' > ')}
          <div style={{flex: 1}} />
          <div
            title="Green if this asset has been materialized since its upstream dependencies."
            style={{
              background: {
                old: 'orange',
                good: 'green',
                none: '#ccc',
              }[computeStatus],
              borderRadius: 7.5,
              width: 15,
              height: 15,
            }}
          />
        </div>
        {definition.description && (
          <div
            style={{
              background: '#EFF4F7',
              padding: '4px 8px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              borderTop: '1px solid #ccc',
              fontSize: 12,
            }}
          >
            {definition.description}
          </div>
        )}
        {event ? (
          <div
            style={{
              background: '#E1EAF0',
              padding: '4px 8px',
              borderTop: '1px solid #ccc',
              fontSize: 12,
              lineHeight: '18px',
            }}
          >
            {runOrError.__typename === 'PipelineRun' && (
              <div style={{display: 'flex', justifyContent: 'space-between'}}>
                <Link
                  data-tooltip={`${runOrError.pipelineName}${
                    runOrError.mode !== 'default' ? `:${runOrError.mode}` : ''
                  }`}
                  data-tooltip-style={RunLinkTooltipStyle}
                  style={{flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: 8}}
                  to={workspacePath(
                    repoAddress.name,
                    repoAddress.location,
                    `jobs/${runOrError.pipelineName}:${runOrError.mode}`,
                  )}
                >
                  {`${runOrError.pipelineName}${
                    runOrError.mode !== 'default' ? `:${runOrError.mode}` : ''
                  }`}
                </Link>
                <Link
                  style={{fontFamily: FontFamily.monospace}}
                  to={`/instance/runs/${runOrError.runId}?${qs.stringify({
                    timestamp: event.stepStats.endTime,
                    selection: event.stepStats.stepKey,
                    logs: `step:${event.stepStats.stepKey}`,
                  })}`}
                  target="_blank"
                >
                  {titleForRun({runId: runOrError.runId})}
                </Link>
              </div>
            )}

            <div style={{display: 'flex', justifyContent: 'space-between'}}>
              {event.stepStats.endTime ? (
                <TimestampDisplay
                  timestamp={event.stepStats.endTime}
                  timeFormat={{showSeconds: false, showTimezone: false}}
                />
              ) : (
                'Never'
              )}
              <TimeElapsed
                startUnix={event.stepStats.startTime}
                endUnix={event.stepStats.endTime}
              />
            </div>
          </div>
        ) : (
          <span></span>
        )}
      </div>
    </ContextMenu>
  );
};

function buildGraphComputeStatuses(graphData: GraphData) {
  const timestamps: {[key: string]: number} = {};
  for (const node of Object.values(graphData.nodes)) {
    timestamps[node.id] =
      node.definition.assetMaterializations[0]?.materializationEvent.stepStats?.startTime || 0;
  }
  const upstream: {[key: string]: string[]} = {};
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);

    downstreamIds.forEach((downstreamId) => {
      upstream[downstreamId] = upstream[downstreamId] || [];
      upstream[downstreamId].push(upstreamId);
    });
  });

  const statuses: {[key: string]: Status} = {};

  for (const asset of Object.values(graphData.nodes)) {
    if (asset.definition.assetMaterializations.length === 0) {
      statuses[asset.id] = 'none';
    }
  }
  for (const asset of Object.values(graphData.nodes)) {
    const id = JSON.stringify(asset.assetKey.path);
    statuses[id] = findComputeStatusForId(timestamps, statuses, upstream, id);
  }
  return statuses;
}

type Status = 'good' | 'old' | 'none';

function findComputeStatusForId(
  timestamps: {[key: string]: number},
  statuses: {[key: string]: Status},
  upstream: {[key: string]: string[]},
  id: string,
): Status {
  const ts = timestamps[id];
  const upstreamIds = upstream[id] || [];
  if (id in statuses) {
    return statuses[id];
  }

  statuses[id] = upstreamIds.some((uid) => timestamps[uid] > ts)
    ? 'old'
    : upstreamIds.some(
        (uid) => findComputeStatusForId(timestamps, statuses, upstream, uid) !== 'good',
      )
    ? 'old'
    : 'good';

  return statuses[id];
}

const RunLinkTooltipStyle = JSON.stringify({
  background: '#E1EAF0',
  padding: '4px 8px',
  marginLeft: -10,
  marginTop: -8,
  fontSize: 13,
  color: Colors.BLUE2,
  border: 0,
  borderRadius: 4,
} as CSSProperties);
