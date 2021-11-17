import { gql, useQuery } from '@apollo/client';
import React from 'react';
import styled from 'styled-components/macro';

import { LATEST_MATERIALIZATION_METADATA_FRAGMENT } from '../../assets/LastMaterializationMetadata';
import { SVGViewport } from '../../graph/SVGViewport';
import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { ExplorerPath } from '../../pipelines/PipelinePathUtils';
import { SidebarPipelineOrJobOverview } from '../../pipelines/SidebarPipelineOrJobOverview';
import { GraphExplorerSolidHandleFragment } from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import { METADATA_ENTRY_FRAGMENT } from '../../runs/MetadataEntry';
import { ColorsWIP } from '../../ui/Colors';
import { Loading } from '../../ui/Loading';
import { NonIdealState } from '../../ui/NonIdealState';
import { SplitPanelContainer } from '../../ui/SplitPanelContainer';
import { repoAddressToSelector } from '../repoAddressToSelector';
import { RepoAddress } from '../types';

import { AssetNode, getNodeDimensions } from './AssetNode';
import { ForeignNode, getForeignNodeDimensions } from './ForeignNode';
import { SidebarAssetInfo } from './SidebarAssetInfo';
import {
  buildGraphComputeStatuses,
  buildGraphData,
  buildSVGPath,
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
  const { repoAddress, handles, selectedHandle, explorerPath, onChangeExplorerPath } = props;
  const repositorySelector = repoAddressToSelector(repoAddress);
  const queryResult = useQuery<AssetGraphQuery, AssetGraphQueryVariables>(ASSETS_GRAPH_QUERY, {
    variables: { repositorySelector },
    notifyOnNetworkStatusChange: true,
  });

  const selectNode = React.useCallback(
    (node: Node | null) => {
      onChangeExplorerPath(
        {
          ...explorerPath,
          opNames: node ? [node.definition.opName!] : [],
          pipelineName: node?.definition.jobName || explorerPath.pipelineName,
        },
        'replace',
      );
    },
    [onChangeExplorerPath, explorerPath],
  );

  useDocumentTitle('Assets');

  return (
    <Loading allowStaleData queryResult={queryResult}>
      {({ repositoryOrError }) => {
        if (repositoryOrError.__typename !== 'Repository') {
          return <NonIdealState icon="error" title="Query Error" />;
        }

        const graphData = buildGraphData(repositoryOrError, explorerPath.pipelineName);
        const hasCycles = graphHasCycles(graphData);

        if (hasCycles) {
          return (
            <NonIdealState
              icon="error"
              title="Cycle detected"
              description="Assets dependencies form a cycle"
            />
          );
        }

        const layout = layoutGraph(graphData);
        const computeStatuses = buildGraphComputeStatuses(graphData);
        const selectedAsset = repositoryOrError.assetNodes.find(
          (a) => a.opName === selectedHandle?.handleID,
        );

        if (!Object.keys(graphData.nodes).length) {
          return (
            <NonIdealState
              icon="no-results"
              title="No assets defined"
              description="No assets defined using the @asset definition"
            />
          );
        }

        return (
          <SplitPanelContainer
            identifier="explorer"
            firstInitialPercent={70}
            firstMinSize={600}
            first={
              <SVGViewport
                interactor={SVGViewport.Interactors.PanAndZoom}
                graphWidth={layout.width}
                graphHeight={layout.height}
                onKeyDown={() => { }}
                onClick={() => selectNode(null)}
                maxZoom={1.2}
                maxAutocenterZoom={1.0}
              >
                {({ scale: _scale }: any) => (
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
                        <path d="M 0 0 L 10 5 L 0 10 z" fill={ColorsWIP.Gray200} />
                      </marker>
                    </defs>
                    <g opacity={0.2}>
                      {layout.edges.map((edge, idx) => (
                        <StyledPath
                          key={idx}
                          d={buildSVGPath({ source: edge.from, target: edge.to })}
                          dashed={edge.dashed}
                          markerEnd="url(#arrow)"
                        />
                      ))}
                    </g>
                    {layout.nodes.map((layoutNode) => {
                      const graphNode = graphData.nodes[layoutNode.id];
                      const { width, height } = graphNode.hidden
                        ? getForeignNodeDimensions(layoutNode.id)
                        : getNodeDimensions(graphNode.definition);
                      return (
                        <foreignObject
                          key={layoutNode.id}
                          x={layoutNode.x}
                          y={layoutNode.y}
                          width={width}
                          height={height}
                          onClick={(e) => {
                            selectNode(graphNode);
                            e.stopPropagation();
                          }}
                        >
                          {graphNode.hidden ? (
                            <ForeignNode assetKey={graphNode.assetKey} />
                          ) : (
                            <AssetNode
                              definition={graphNode.definition}
                              handle={
                                handles.find((h) => h.handleID === graphNode.definition.opName)!
                              }
                              secondaryHighlight={false}
                              selected={selectedAsset === graphNode.definition}
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
              selectedAsset && selectedHandle ? (
                <SidebarAssetInfo
                  node={selectedAsset}
                  handle={selectedHandle}
                  repoAddress={repoAddress}
                />
              ) : (
                <SidebarPipelineOrJobOverview
                  repoAddress={repoAddress}
                  explorerPath={explorerPath}
                />
              )
            }
          />
        );
      }}
    </Loading>
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
            ...LatestMaterializationMetadataFragment

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
          inProgressRuns {
            runId
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
  ${LATEST_MATERIALIZATION_METADATA_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
const StyledPath = styled('path') <{ dashed: boolean }>`
  stroke-width: 4;
  stroke: ${ColorsWIP.Gray600};
  ${({ dashed }) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;
