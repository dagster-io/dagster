import {gql, useQuery} from '@apollo/client';
import {
  Alert,
  Box,
  ButtonLink,
  Colors,
  NonIdealState,
  Spinner,
  Tab,
  Tabs,
  Tag,
} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {Timestamp} from '../app/time/Timestamp';
import {GraphData, LiveDataForNode, toGraphId, tokenForAssetKey} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {StaleTag} from '../assets/StaleTag';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepositoryLink} from '../nav/RepositoryLink';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetEvents} from './AssetEvents';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {AssetNodeInstigatorTag, ASSET_NODE_INSTIGATORS_FRAGMENT} from './AssetNodeInstigatorTag';
import {AssetNodeLineage} from './AssetNodeLineage';
import {AssetLineageScope} from './AssetNodeLineageGraph';
import {AssetPageHeader} from './AssetPageHeader';
import {AssetPartitions} from './AssetPartitions';
import {AssetPlots} from './AssetPlots';
import {CurrentMinutesLateTag} from './CurrentMinutesLateTag';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {AssetKey} from './types';
import {
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables,
  AssetViewDefinitionQuery_assetOrError_Asset_definition,
} from './types/AssetViewDefinitionQuery';

interface Props {
  assetKey: AssetKey;
}

export interface AssetViewParams {
  view?: 'events' | 'definition' | 'lineage' | 'overview' | 'plots' | 'partitions';
  lineageScope?: AssetLineageScope;
  lineageDepth?: number;
  partition?: string;
  time?: string;
  asOf?: string;
}

export const AssetView: React.FC<Props> = ({assetKey}) => {
  const [params, setParams] = useQueryPersistedState<AssetViewParams>({});

  // Load the asset definition
  const {definition, definitionQueryResult, lastMaterialization} = useAssetViewAssetDefinition(
    assetKey,
  );

  const defaultTab = definition?.partitionDefinition ? 'partitions' : 'events';
  const selectedTab = params.view || defaultTab;

  // Load the asset graph - a large graph for the Lineage tab, a small graph for the Definition tab
  // tab, or just the current node for other tabs. NOTE: Changing the query does not re-fetch data,
  // it just re-filters.
  const visible = getQueryForVisibleAssets(assetKey, params);
  const visibleAssetGraph = useAssetGraphData(visible.query, {
    hideEdgesToNodesOutsideQuery: true,
  });

  const {upstream, downstream} = useNeighborsFromGraph(visibleAssetGraph.assetGraphData, assetKey);

  // Observe the live state of the visible assets. Note: We use the "last materialization"
  // provided by this hook to trigger resets of the datasets inside the Activity / Plots tabs
  const {liveDataRefreshState, liveDataByNode, runWatchers} = useLiveDataForAssetKeys(
    visibleAssetGraph.graphAssetKeys,
  );

  // The "live" data is preferable and more current, but only available for SDAs. Fallback
  // to the materialization timestamp we loaded from assetOrError if live data is not available.
  const lastMaterializedAt = (
    liveDataByNode[toGraphId(assetKey)]?.lastMaterialization || lastMaterialization
  )?.timestamp;

  const viewingMostRecent = !params.asOf || Number(lastMaterializedAt) <= Number(params.asOf);

  const refreshState = useMergedRefresh(
    useQueryRefreshAtInterval(definitionQueryResult, FIFTEEN_SECONDS),
    liveDataRefreshState,
  );

  const renderDefinitionTab = () => {
    if (!definition) {
      return <AssetNoDefinitionState />;
    }
    return (
      <AssetNodeDefinition
        assetNode={definition}
        upstream={upstream}
        downstream={downstream}
        liveDataByNode={liveDataByNode}
      />
    );
  };

  const renderLineageTab = () => {
    if (!definition) {
      return <AssetNoDefinitionState />;
    }
    if (!visibleAssetGraph.assetGraphData) {
      return (
        <Box style={{flex: 1}} flex={{alignItems: 'center', justifyContent: 'center'}}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    return (
      <AssetNodeLineage
        params={params}
        setParams={setParams}
        assetNode={definition}
        liveDataByNode={liveDataByNode}
        requestedDepth={visible.requestedDepth}
        assetGraphData={visibleAssetGraph.assetGraphData}
        graphQueryItems={visibleAssetGraph.graphQueryItems}
      />
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', width: '100%', overflowY: 'auto'}}>
      {runWatchers}
      <AssetPageHeader
        assetKey={assetKey}
        tags={
          <AssetViewPageHeaderTags
            definition={definition}
            liveData={liveDataByNode[toGraphId(assetKey)]}
            onShowUpstream={() => setParams({...params, view: 'lineage', lineageScope: 'upstream'})}
          />
        }
        tabs={
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
            <Tabs size="large" selectedTabId={selectedTab}>
              {definition?.partitionDefinition && (
                <Tab
                  id="partitions"
                  title="Partitions"
                  onClick={() => setParams({...params, view: 'partitions'})}
                />
              )}
              <Tab
                id="events"
                title="Events"
                onClick={() => setParams({...params, view: 'events'})}
              />
              <Tab id="plots" title="Plots" onClick={() => setParams({...params, view: 'plots'})} />
              <Tab
                id="definition"
                title="Definition"
                onClick={() => setParams({...params, view: 'definition'})}
                disabled={!definition}
              />
              <Tab
                id="lineage"
                title="Lineage"
                onClick={() => setParams({...params, view: 'lineage'})}
                disabled={!definition}
              />
            </Tabs>
            {refreshState && (
              <Box padding={{bottom: 8}}>
                <QueryRefreshCountdown refreshState={refreshState} />
              </Box>
            )}
          </Box>
        }
        right={
          <Box style={{margin: '-4px 0'}}>
            {definition && definition.jobNames.length > 0 && upstream && (
              <LaunchAssetExecutionButton allAssetKeys={[definition.assetKey]} />
            )}
          </Box>
        }
      />
      {!viewingMostRecent && (
        <HistoricalViewAlert
          asOf={params.asOf}
          onClick={() => setParams({asOf: undefined, time: params.asOf})}
          hasDefinition={!!definition}
        />
      )}

      {
        // Avoid thrashing the events UI (which chooses a different default query based on whether
        // data is partitioned) by waiting for the definition to be loaded before we show any tab content
      }
      {definitionQueryResult.loading && !definitionQueryResult.previousData ? (
        <Box
          style={{height: 390}}
          flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
        >
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          {selectedTab === 'definition' ? (
            renderDefinitionTab()
          ) : selectedTab === 'lineage' ? (
            renderLineageTab()
          ) : selectedTab === 'partitions' ? (
            <AssetPartitions
              assetKey={assetKey}
              assetPartitionNames={definition?.partitionKeysByDimension.map((k) => k.name)}
              assetLastMaterializedAt={lastMaterializedAt}
              params={params}
              paramsTimeWindowOnly={!!params.asOf}
              setParams={setParams}
              liveData={definition ? liveDataByNode[toGraphId(definition.assetKey)] : undefined}
            />
          ) : selectedTab === 'events' ? (
            <AssetEvents
              assetKey={assetKey}
              assetHasDefinedPartitions={!!definition?.partitionDefinition}
              assetLastMaterializedAt={lastMaterializedAt}
              params={params}
              paramsTimeWindowOnly={!!params.asOf}
              setParams={setParams}
              liveData={definition ? liveDataByNode[toGraphId(definition.assetKey)] : undefined}
            />
          ) : selectedTab === 'plots' ? (
            <AssetPlots
              assetKey={assetKey}
              assetHasDefinedPartitions={!!definition?.partitionDefinition}
              params={params}
              setParams={setParams}
            />
          ) : (
            <span />
          )}
        </>
      )}
    </Box>
  );
};

const AssetNoDefinitionState = () => (
  <Box padding={{vertical: 32}}>
    <NonIdealState
      title="No definition"
      description="This asset doesn't have a software definition in any of your loaded repositories."
      icon="materialization"
    />
  </Box>
);

// This is a helper method that returns the "asset graph query string" for the current
// AssetView tab + page settings. eg:
// - If you're viewing the "Lineage > Upstream 4 layers", it returns `++++token`
// - If you're viewing the definition tab, it returns  "+token+" (upstream, downstream are visible)
// - If you're viewing the overview / events tabs, it just returns "token"
//
function getQueryForVisibleAssets(assetKey: AssetKey, params: AssetViewParams) {
  const token = tokenForAssetKey(assetKey);

  if (params.view === 'definition') {
    return {query: `+"${token}"+`, requestedDepth: 1};
  }
  if (params.view === 'lineage') {
    const defaultDepth = params.lineageScope === 'neighbors' ? 2 : 5;
    const requestedDepth = Number(params.lineageDepth) || defaultDepth;
    const depthStr = '+'.repeat(requestedDepth);

    // Load the asset lineage (for both lineage tab and definition "Upstream" / "Downstream")
    const query =
      params.view === 'lineage' && params.lineageScope === 'upstream'
        ? `${depthStr}"${token}"`
        : params.view === 'lineage' && params.lineageScope === 'downstream'
        ? `"${token}"${depthStr}`
        : `${depthStr}"${token}"${depthStr}`;

    return {
      query,
      requestedDepth,
    };
  }
  return {query: `"${token}"`, requestedDepth: 0};
}

function useNeighborsFromGraph(graphData: GraphData | null, assetKey: AssetKey) {
  const graphId = toGraphId(assetKey);

  return React.useMemo(() => {
    if (!graphData) {
      return {upstream: null, downstream: null};
    }
    return {
      upstream: Object.values(graphData.nodes)
        .filter((n) => graphData.upstream[graphId]?.[toGraphId(n.assetKey)])
        .map((n) => n.definition),
      downstream: Object.values(graphData.nodes)
        .filter((n) => graphData.downstream[graphId]?.[toGraphId(n.assetKey)])
        .map((n) => n.definition),
    };
  }, [graphData, graphId]);
}

const useAssetViewAssetDefinition = (assetKey: AssetKey) => {
  const result = useQuery<AssetViewDefinitionQuery, AssetViewDefinitionQueryVariables>(
    ASSET_VIEW_DEFINITION_QUERY,
    {
      variables: {assetKey: {path: assetKey.path}},
      notifyOnNetworkStatusChange: true,
    },
  );
  const {assetOrError} = result.data || result.previousData || {};
  const asset = assetOrError && assetOrError.__typename === 'Asset' ? assetOrError : null;
  return {
    definitionQueryResult: result,
    definition: asset?.definition || null,
    lastMaterialization: asset?.assetMaterializations[0],
  };
};

const ASSET_VIEW_DEFINITION_QUERY = gql`
  query AssetViewDefinitionQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetMaterializations(limit: 1) {
          timestamp
        }
        definition {
          id
          groupName
          partitionDefinition {
            description
          }
          partitionKeysByDimension {
            name
          }
          repository {
            id
            name
            location {
              id
              name
            }
          }

          ...AssetNodeInstigatorsFragment
          ...AssetNodeDefinitionFragment
        }
      }
    }
  }
  ${ASSET_NODE_INSTIGATORS_FRAGMENT}
  ${ASSET_NODE_DEFINITION_FRAGMENT}
`;

const HistoricalViewAlert: React.FC<{
  asOf: string | undefined;
  onClick: () => void;
  hasDefinition: boolean;
}> = ({asOf, onClick, hasDefinition}) => (
  <Box
    padding={{vertical: 16, horizontal: 24}}
    border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
  >
    <Alert
      intent="info"
      title={
        <span>
          This is a historical view of materializations as of{' '}
          <span style={{fontWeight: 600}}>
            <Timestamp
              timestamp={{ms: Number(asOf)}}
              timeFormat={{showSeconds: true, showTimezone: true}}
            />
          </span>
          .
        </span>
      }
      description={
        <ButtonLink onClick={onClick} underline="always">
          {hasDefinition
            ? 'Show definition and latest materializations'
            : 'Show latest materializations'}
        </ButtonLink>
      }
    />
  </Box>
);

const AssetViewPageHeaderTags: React.FC<{
  definition: AssetViewDefinitionQuery_assetOrError_Asset_definition | null;
  liveData?: LiveDataForNode;
  onShowUpstream: () => void;
}> = ({definition, liveData, onShowUpstream}) => {
  const repoAddress = definition
    ? buildRepoAddress(definition.repository.name, definition.repository.location.name)
    : null;

  return (
    <>
      {definition && repoAddress ? (
        <Tag icon="asset">
          Asset in <RepositoryLink repoAddress={repoAddress} />
        </Tag>
      ) : (
        <Tag icon="asset_non_sda">Asset</Tag>
      )}
      {definition && repoAddress && (
        <AssetNodeInstigatorTag assetNode={definition} repoAddress={repoAddress} />
      )}
      {definition && repoAddress && definition.groupName && (
        <Tag icon="asset_group">
          <Link to={workspacePathFromAddress(repoAddress, `/asset-groups/${definition.groupName}`)}>
            {definition.groupName}
          </Link>
        </Tag>
      )}
      {liveData?.freshnessPolicy && <CurrentMinutesLateTag liveData={liveData} policyOnHover />}
      <StaleTag liveData={liveData} onClick={onShowUpstream} />
    </>
  );
};
