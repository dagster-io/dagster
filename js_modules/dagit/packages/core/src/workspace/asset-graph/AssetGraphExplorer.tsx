import {gql, useQuery} from '@apollo/client';
import {uniq, without} from 'lodash';
import React from 'react';
import styled from 'styled-components/macro';

import {filterByQuery} from '../../app/GraphQueryImpl';
import {LATEST_MATERIALIZATION_METADATA_FRAGMENT} from '../../assets/LastMaterializationMetadata';
import {LaunchRootExecutionButton} from '../../execute/LaunchRootExecutionButton';
import {SVGViewport} from '../../graph/SVGViewport';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {ExplorerPath} from '../../pipelines/PipelinePathUtils';
import {SidebarPipelineOrJobOverview} from '../../pipelines/SidebarPipelineOrJobOverview';
import {GraphExplorerSolidHandleFragment} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {GraphQueryInput} from '../../ui/GraphQueryInput';
import {Loading} from '../../ui/Loading';
import {NonIdealState} from '../../ui/NonIdealState';
import {SplitPanelContainer} from '../../ui/SplitPanelContainer';
import {repoAddressToSelector} from '../repoAddressToSelector';
import {RepoAddress} from '../types';

import {AssetLinks} from './AssetLinks';
import {AssetNode, ASSET_NODE_FRAGMENT, getNodeDimensions} from './AssetNode';
import {ForeignNode, getForeignNodeDimensions} from './ForeignNode';
import {SidebarAssetInfo} from './SidebarAssetInfo';
import {
  buildGraphComputeStatuses,
  buildGraphData,
  GraphData,
  graphHasCycles,
  layoutGraph,
  Node,
} from './Utils';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
  AssetGraphQuery_repositoryOrError_Repository_assetNodes,
} from './types/AssetGraphQuery';

type AssetNode = AssetGraphQuery_repositoryOrError_Repository_assetNodes;

interface Props {
  repoAddress: RepoAddress;
  explorerPath: ExplorerPath;
  handles: GraphExplorerSolidHandleFragment[];
  selectedHandle?: GraphExplorerSolidHandleFragment;
  onChangeExplorerPath: (path: ExplorerPath, mode: 'replace' | 'push') => void;
}

export const AssetGraphExplorer: React.FC<Props> = (props) => {
  const {repoAddress, explorerPath} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSETS_GRAPH_QUERY, {
    variables: {repositorySelector},
    notifyOnNetworkStatusChange: true,
  });

  useDocumentTitle('Assets');

  const graphData = React.useMemo(() => {
    const repositoryOrError =
      queryResult.data?.repositoryOrError.__typename === 'Repository'
        ? queryResult.data?.repositoryOrError
        : null;
    if (!repositoryOrError) {
      return null;
    }
    return buildGraphData(repositoryOrError, explorerPath.pipelineName);
  }, [queryResult, explorerPath.pipelineName]);

  return (
    <Loading allowStaleData queryResult={queryResult}>
      {({repositoryOrError}) => {
        if (repositoryOrError.__typename !== 'Repository' || !graphData) {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        if (graphHasCycles(graphData)) {
          return (
            <NonIdealState
              icon="error"
              title="Cycle detected"
              description="Assets dependencies form a cycle"
            />
          );
        }
        if (!Object.keys(graphData.nodes).length) {
          return (
            <NonIdealState
              icon="no-results"
              title="No assets defined"
              description="No assets defined using the @asset definition"
            />
          );
        }

        return <AssetGraphExplorerWithData graphData={graphData} {...props} />;
      }}
    </Loading>
  );
};

const AssetGraphExplorerWithData: React.FC<
  {graphData: ReturnType<typeof buildGraphData>} & Props
> = (props) => {
  const {
    repoAddress,
    handles,
    selectedHandle,
    explorerPath,
    onChangeExplorerPath,
    graphData,
  } = props;

  const selectedDefinition = selectedHandle?.solid.definition;
  const selectedGraphNode =
    selectedDefinition &&
    Object.values(graphData.nodes).find(
      (node) => node.definition.opName === selectedDefinition.name,
    );

  const onSelectNode = React.useCallback(
    (e: React.MouseEvent<any>, node: Node) => {
      e.stopPropagation();

      const {opName, jobName} = node.definition;
      if (!opName) {
        return;
      }

      const append = jobName === explorerPath.pipelineName && (e.shiftKey || e.metaKey);
      const existing = explorerPath.opsQuery.split(',');
      const added =
        e.shiftKey && selectedGraphNode
          ? opsInRange({graph: graphData, from: selectedGraphNode, to: node})
          : [opName];

      const next = append
        ? (existing.includes(opName)
            ? without(existing, opName)
            : uniq([...existing, ...added])
          ).join(',')
        : `${opName}`;

      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: [opName],
          opsQuery: next,
          pipelineName: jobName || explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [explorerPath, selectedGraphNode, graphData, onChangeExplorerPath],
  );

  const {all: highlighted} = React.useMemo(
    () =>
      filterByQuery(
        handles.map((h) => h.solid),
        explorerPath.opsQuery,
      ),
    [explorerPath.opsQuery, handles],
  );

  const layout = React.useMemo(() => layoutGraph(graphData), [graphData]);
  const computeStatuses = React.useMemo(() => buildGraphComputeStatuses(graphData), [graphData]);

  return (
    <SplitPanelContainer
      identifier="explorer"
      firstInitialPercent={70}
      firstMinSize={600}
      first={
        <>
          <SVGViewport
            interactor={SVGViewport.Interactors.PanAndZoom}
            graphWidth={layout.width}
            graphHeight={layout.height}
            onKeyDown={() => {}}
            onClick={() =>
              onChangeExplorerPath(
                {
                  ...explorerPath,
                  pipelineName: explorerPath.pipelineName,
                  opsQuery: '',
                  opNames: [],
                },
                'replace',
              )
            }
            maxZoom={1.2}
            maxAutocenterZoom={1.0}
          >
            {({scale: _scale}, bounds) => (
              <SVGContainer width={layout.width} height={layout.height}>
                <AssetLinks edges={layout.edges} />

                {layout.nodes.map((layoutNode) => {
                  const graphNode = graphData.nodes[layoutNode.id];
                  const {width, height} = graphNode.hidden
                    ? getForeignNodeDimensions(layoutNode.id)
                    : getNodeDimensions(graphNode.definition);

                  if (
                    layoutNode.x + width < bounds.left ||
                    layoutNode.y + height < bounds.top ||
                    layoutNode.x > bounds.right ||
                    layoutNode.y > bounds.bottom
                  ) {
                    return null;
                  }

                  return (
                    <foreignObject
                      key={layoutNode.id}
                      x={layoutNode.x}
                      y={layoutNode.y}
                      width={width}
                      height={height}
                      onClick={(e) => onSelectNode(e, graphNode)}
                      style={{overflow: 'visible'}}
                    >
                      {graphNode.hidden ? (
                        <ForeignNode assetKey={graphNode.assetKey} />
                      ) : (
                        <AssetNode
                          definition={graphNode.definition}
                          metadata={
                            handles.find((h) => h.handleID === graphNode.definition.opName)!.solid
                              .definition.metadata
                          }
                          selected={selectedGraphNode === graphNode}
                          computeStatus={computeStatuses[graphNode.id]}
                          repoAddress={repoAddress}
                          secondaryHighlight={
                            explorerPath.opsQuery
                              ? highlighted.some(
                                  (h) => h.definition.name === graphNode.definition.opName,
                                )
                              : false
                          }
                        />
                      )}
                    </foreignObject>
                  );
                })}
              </SVGContainer>
            )}
          </SVGViewport>

          <AssetQueryInputContainer>
            <GraphQueryInput
              items={handles.map((h) => h.solid)}
              value={explorerPath.opsQuery}
              placeholder="Type an asset subset…"
              onChange={(opsQuery) => onChangeExplorerPath({...explorerPath, opsQuery}, 'replace')}
            />
            <LaunchRootExecutionButton
              pipelineName={explorerPath.pipelineName}
              disabled={!explorerPath.opsQuery || highlighted.length === 0}
              getVariables={() => ({
                executionParams: {
                  mode: 'default',
                  executionMetadata: {},
                  runConfigData: {},
                  selector: {
                    ...repoAddressToSelector(repoAddress),
                    pipelineName: explorerPath.pipelineName,
                    solidSelection: highlighted.map((h) => h.name),
                  },
                },
              })}
            />
          </AssetQueryInputContainer>
        </>
      }
      second={
        selectedGraphNode && selectedDefinition ? (
          <SidebarAssetInfo
            node={selectedGraphNode.definition}
            definition={selectedDefinition}
            repoAddress={repoAddress}
          />
        ) : (
          <SidebarPipelineOrJobOverview repoAddress={repoAddress} explorerPath={explorerPath} />
        )
      }
    />
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
        assetNodes {
          ...AssetNodeFragment
          id
          assetKey {
            path
          }
          dependencies {
            inputName
            upstreamAsset {
              id
              assetKey {
                path
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
  ${ASSET_NODE_FRAGMENT}
  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;

const AssetQueryInputContainer = styled.div`
  z-index: 2;
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  display: flex;
`;

const opsInRange = (
  {graph, from, to}: {graph: GraphData; from: Node; to: Node},
  seen: string[] = [],
) => {
  if (!from) {
    return [];
  }
  if (from.id === to.id) {
    return [to.definition.opName!];
  }
  const adjacent = [
    ...Object.keys(graph.upstream[from.id] || {}),
    ...Object.keys(graph.downstream[from.id] || {}),
  ].map((n) => graph.nodes[n]);

  let best: string[] = [];

  for (const node of adjacent) {
    if (seen.includes(node.id)) {
      continue;
    }
    const result: string[] = opsInRange({graph, from: node, to}, [...seen, from.id]);
    if (result.length && (best.length === 0 || result.length < best.length)) {
      best = [from.definition.opName!, ...result];
    }
  }
  return best;
};
