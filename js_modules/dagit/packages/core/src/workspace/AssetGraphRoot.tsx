import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import {pathVerticalDiagonal} from '@vx/shape';
import * as dagre from 'dagre';
import React, {CSSProperties} from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SVGViewport} from '../graph/SVGViewport';
import {Description} from '../pipelines/Description';
import {SidebarSection} from '../pipelines/SidebarComponents';
import {METADATA_ENTRY_FRAGMENT} from '../runs/MetadataEntry';
import {titleForRun} from '../runs/RunUtils';
import {TimeElapsed} from '../runs/TimeElapsed';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {Box} from '../ui/Box';
import {Loading} from '../ui/Loading';
import {PageHeader} from '../ui/PageHeader';
import {SplitPanelContainer} from '../ui/SplitPanelContainer';
import {FontFamily} from '../ui/styles';
import {Heading} from '../ui/Text';

import {repoAddressToSelector} from './repoAddressToSelector';
import {RepoAddress} from './types';
import {
  AssetGraphQuery_repositoryOrError_Repository_assetDefinitions,
  AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetKey,
} from './types/AssetGraphQuery';

type AssetDefinition = AssetGraphQuery_repositoryOrError_Repository_assetDefinitions;
type AssetKey = AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetKey;

interface Props extends RouteComponentProps {
  repoAddress: RepoAddress;
}

interface Node {
  id: string;
  assetKey: AssetKey;
  definition: AssetDefinition;
}
interface LayoutNode {
  id: string;
  x: number;
  y: number;
}
interface GraphData {
  nodes: {[id: string]: Node};
  downstream: {[upstream: string]: {[downstream: string]: string}};
}
interface IPoint {
  x: number;
  y: number;
}
export type IEdge = {
  from: IPoint;
  to: IPoint;
  dashed: boolean;
};

const getNodeDimensions = (def: AssetDefinition) => {
  let height = 40;
  if (def.description) {
    height += 25;
  }
  if (def.assetMaterializations.length) {
    height += 60;
  }
  return {width: Math.max(250, def.assetKey.path.join('>').length * 9.5), height};
};

const buildGraphData = (assetDefinitions: AssetDefinition[]) => {
  const nodes: {[id: string]: {id: string; assetKey: AssetKey; definition: AssetDefinition}} = {};
  const downstream: {[downstreamId: string]: {[upstreamId: string]: string}} = {};

  assetDefinitions.forEach((definition) => {
    const assetKeyJson = JSON.stringify(definition.assetKey.path);
    nodes[assetKeyJson] = {
      id: assetKeyJson,
      assetKey: definition.assetKey,
      definition,
    };
    definition.dependencies.forEach((dependency) => {
      const upstreamAssetKeyJson = JSON.stringify(dependency.upstreamAsset.assetKey.path);
      downstream[upstreamAssetKeyJson] = {
        ...(downstream[upstreamAssetKeyJson] || {}),
        [assetKeyJson]: dependency.inputName,
      };
    });
  });

  return {nodes, downstream};
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

  Object.values(graphData.nodes).forEach((node) => {
    g.setNode(node.id, getNodeDimensions(node.definition));
  });
  Object.keys(graphData.downstream).forEach((upstreamId) => {
    const downstreamIds = Object.keys(graphData.downstream[upstreamId]);
    downstreamIds.forEach((downstreamId) => {
      g.setEdge({v: upstreamId, w: downstreamId}, {weight: 1});
    });
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
  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery(ASSETS_GRAPH_QUERY, {
    variables: {repositorySelector},
    notifyOnNetworkStatusChange: true,
  });
  const [nodeSelection, setSelectedNode] = React.useState<Node | undefined>();

  const selectNode = (node: Node) => {
    setSelectedNode(node);
  };

  // Show the name of the composite solid we are within (-1 is the selection, -2 is current parent)
  // or the name of the pipeline tweaked to look a bit more like a graph name.

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%'}}>
      <Box padding={24}>
        <PageHeader title={<Heading>Assets</Heading>} />
      </Box>
      <div style={{flex: 1, display: 'flex', borderTop: '1px solid #ececec'}}>
        <SplitPanelContainer
          identifier="assets"
          firstInitialPercent={70}
          firstMinSize={600}
          first={
            <Loading allowStaleData queryResult={queryResult}>
              {({repositoryOrError}) => {
                if (repositoryOrError.__typename !== 'Repository') {
                  return null;
                }
                const graphData = buildGraphData(repositoryOrError.assetDefinitions);
                const hasCycles = graphHasCycles(graphData);
                const layout = hasCycles ? null : layoutGraph(graphData);
                return layout ? (
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
                          const {width, height} = getNodeDimensions(graphNode.definition);
                          return (
                            <foreignObject
                              key={layoutNode.id}
                              x={layoutNode.x}
                              y={layoutNode.y}
                              width={width}
                              height={height}
                              onClick={() => selectNode(graphNode)}
                            >
                              <AssetNode
                                definition={graphNode.definition}
                                selected={nodeSelection?.id === graphNode.id}
                              />
                            </foreignObject>
                          );
                        })}
                      </SVGContainer>
                    )}
                  </SVGViewport>
                ) : null;
              }}
            </Loading>
          }
          second={
            nodeSelection ? (
              <AssetPanel node={nodeSelection} />
            ) : (
              <NonIdealState
                title="No asset selected"
                description="Select an asset to see its definition and ops."
              />
            )
          }
        />
      </div>
    </Box>
  );
};

const AssetPanel = ({node}: {node: Node}) => {
  return (
    <>
      <Box margin={32} style={{fontWeight: 'bold', fontSize: 18}}>
        {node.assetKey.path.join(' > ')}
      </Box>
      <SidebarSection title="Description">
        <Description description={node.definition.description || null} />
      </SidebarSection>
      <SidebarSection title="Jobs">
        {node.definition.jobNames
          ? node.definition.jobNames.map((name) => <div key={name}>{name}</div>)
          : null}
      </SidebarSection>
    </>
  );
};

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
        assetDefinitions {
          id
          assetKey {
            path
          }
          opName
          description
          jobNames
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
              }
            }
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

const AssetNode: React.FC<{
  definition: AssetDefinition;
  selected: boolean;
}> = ({definition, selected}) => {
  const {materializationEvent: event, runOrError} = definition.assetMaterializations[0] || {};

  return (
    <div
      style={{
        border: '1px solid #ececec',
        outline: selected ? `2px solid ${Colors.BLUE4}` : 'none',
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
          <div style={{display: 'flex', justifyContent: 'space-between'}}>
            <div>Elapsed Time: </div>
            <TimeElapsed startUnix={event.stepStats.startTime} endUnix={event.stepStats.endTime} />
          </div>
          <div style={{display: 'flex', justifyContent: 'space-between'}}>
            <div>Materialized: </div>
            {event.stepStats.endTime ? (
              <TimestampDisplay
                timestamp={event.stepStats.endTime}
                timeFormat={{showSeconds: false, showTimezone: false}}
              />
            ) : (
              'Never'
            )}
          </div>
          <div style={{display: 'flex', justifyContent: 'space-between'}}>
            <div>Run: </div>
            {runOrError.__typename === 'PipelineRun' ? (
              <Link
                style={{fontFamily: FontFamily.monospace}}
                to={`/instance/runs/${runOrError.runId}?timestamp=${event.stepStats.endTime}`}
                target="_blank"
              >
                {titleForRun({runId: runOrError.runId})}
              </Link>
            ) : (
              'Not Found'
            )}
          </div>
        </div>
      ) : (
        <span></span>
      )}
    </div>
  );
};
