import {gql, useQuery} from '@apollo/client';
import {Alert, Box, NonIdealState, Spinner, Tag, ErrorBoundary} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link, useLocation} from 'react-router-dom';

import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useMergedRefresh,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {Timestamp} from '../app/time/Timestamp';
import {
  GraphData,
  LiveDataForNode,
  nodeDependsOnSelf,
  toGraphId,
  tokenForAssetKey,
} from '../asset-graph/Utils';
import {useAssetGraphData} from '../asset-graph/useAssetGraphData';
import {useLiveDataForAssetKeys} from '../asset-graph/useLiveDataForAssetKeys';
import {StaleReasonsTags} from '../assets/Stale';
import {AssetComputeKindTag} from '../graph/OpTags';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {RepositoryLink} from '../nav/RepositoryLink';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetEvents} from './AssetEvents';
import {AssetFeatureContext} from './AssetFeatureContext';
import {AssetNodeDefinition, ASSET_NODE_DEFINITION_FRAGMENT} from './AssetNodeDefinition';
import {AssetNodeInstigatorTag, ASSET_NODE_INSTIGATORS_FRAGMENT} from './AssetNodeInstigatorTag';
import {AssetNodeLineage} from './AssetNodeLineage';
import {AssetPageHeader} from './AssetPageHeader';
import {AssetPartitions} from './AssetPartitions';
import {AssetPlots} from './AssetPlots';
import {AssetTabs} from './AssetTabs';
import {AssetAutomaterializePolicyPage} from './AutoMaterializePolicyPage/AssetAutomaterializePolicyPage';
import {AutomaterializeDaemonStatusTag} from './AutomaterializeDaemonStatusTag';
import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {LaunchAssetObservationButton} from './LaunchAssetObservationButton';
import {OverdueTag} from './OverdueTag';
import {UNDERLYING_OPS_ASSET_NODE_FRAGMENT} from './UnderlyingOpsOrGraph';
import {AssetChecks} from './asset-checks/AssetChecks';
import {AssetKey, AssetViewParams} from './types';
import {
  AssetViewDefinitionQuery,
  AssetViewDefinitionQueryVariables,
  AssetViewDefinitionNodeFragment,
} from './types/AssetView.types';
import {healthRefreshHintFromLiveData} from './usePartitionHealthData';
import {useReportEventsModal} from './useReportEventsModal';

interface Props {
  assetKey: AssetKey;
}

export const AssetView = ({assetKey}: Props) => {
  const [params, setParams] = useQueryPersistedState<AssetViewParams>({});
  const {tabBuilder, renderFeatureView} = React.useContext(AssetFeatureContext);

  // Load the asset definition
  const {definition, definitionQueryResult, lastMaterialization} =
    useAssetViewAssetDefinition(assetKey);
  const tabList = React.useMemo(
    () => tabBuilder({definition, params}),
    [definition, params, tabBuilder],
  );

  const defaultTab = tabList.some((t) => t.id === 'partitions') ? 'partitions' : 'events';
  const selectedTab = params.view || defaultTab;

  // Load the asset graph - a large graph for the Lineage tab, a small graph for the Definition tab
  // tab, or just the current node for other tabs. NOTE: Changing the query does not re-fetch data,
  // it just re-filters.
  const visible = getQueryForVisibleAssets(assetKey, params);
  const visibleAssetGraph = useAssetGraphData(visible.query, {
    hideEdgesToNodesOutsideQuery: true,
  });

  const {upstream, downstream} = useNeighborsFromGraph(visibleAssetGraph.assetGraphData, assetKey);
  const node = visibleAssetGraph.assetGraphData?.nodes[toGraphId(assetKey)];

  // Observe the live state of the visible assets. Note: We use the "last materialization"
  // provided by this hook to trigger resets of the datasets inside the Activity / Plots tabs
  const {liveDataRefreshState, liveDataByNode} = useLiveDataForAssetKeys(
    visibleAssetGraph.graphAssetKeys,
  );

  // The "live" data is preferable and more current, but only available for SDAs. Fallback
  // to the materialization timestamp we loaded from assetOrError if live data is not available.
  const liveDataForAsset: LiveDataForNode | undefined = liveDataByNode[toGraphId(assetKey)];
  const lastMaterializedAt = (liveDataForAsset?.lastMaterialization || lastMaterialization)
    ?.timestamp;

  const viewingMostRecent = !params.asOf || Number(lastMaterializedAt) <= Number(params.asOf);

  // Some tabs make expensive queries that should be refreshed after materializations or failures.
  // We build a hint string from the live summary info and refresh the views when the hint changes.
  const dataRefreshHint = liveDataForAsset
    ? healthRefreshHintFromLiveData(liveDataForAsset)
    : lastMaterialization?.timestamp;

  const refreshState = useMergedRefresh(
    useQueryRefreshAtInterval(definitionQueryResult, FIFTEEN_SECONDS),
    liveDataRefreshState,
  );

  const renderDefinitionTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    if (!definition) {
      return <AssetNoDefinitionState />;
    }
    return (
      <AssetNodeDefinition
        assetNode={definition}
        upstream={upstream}
        downstream={downstream}
        dependsOnSelf={node ? nodeDependsOnSelf(node) : false}
      />
    );
  };

  const renderLineageTab = () => {
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
        assetKey={assetKey}
        liveDataByNode={liveDataByNode}
        requestedDepth={visible.requestedDepth}
        assetGraphData={visibleAssetGraph.assetGraphData}
        graphQueryItems={visibleAssetGraph.graphQueryItems}
      />
    );
  };

  const renderPartitionsTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetPartitions
        assetKey={assetKey}
        assetPartitionDimensions={definition?.partitionKeysByDimension.map((k) => k.name)}
        dataRefreshHint={dataRefreshHint}
        params={params}
        paramsTimeWindowOnly={!!params.asOf}
        setParams={setParams}
      />
    );
  };

  const renderEventsTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetEvents
        assetKey={assetKey}
        assetNode={definition}
        dataRefreshHint={dataRefreshHint}
        params={params}
        paramsTimeWindowOnly={!!params.asOf}
        setParams={setParams}
        liveData={definition ? liveDataByNode[toGraphId(definition.assetKey)] : undefined}
      />
    );
  };

  const renderPlotsTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetPlots
        assetKey={assetKey}
        assetHasDefinedPartitions={!!definition?.partitionDefinition}
        params={params}
        setParams={setParams}
      />
    );
  };

  const renderAutomaterializeHistoryTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetAutomaterializePolicyPage
        assetKey={assetKey}
        assetHasDefinedPartitions={!!definition?.partitionDefinition}
      />
    );
  };

  const renderChecksTab = () => {
    if (definitionQueryResult.loading && !definitionQueryResult.previousData) {
      return <AssetLoadingDefinitionState />;
    }
    return (
      <AssetChecks
        assetKey={assetKey}
        lastMaterializationTimestamp={lastMaterialization?.timestamp}
      />
    );
  };

  const renderContent = () => {
    switch (selectedTab) {
      case 'definition':
        return renderDefinitionTab();
      case 'lineage':
        return renderLineageTab();
      case 'partitions':
        return renderPartitionsTab();
      case 'events':
        return renderEventsTab();
      case 'plots':
        return renderPlotsTab();
      case 'auto-materialize-history':
        return renderAutomaterializeHistoryTab();
      case 'checks':
        return renderChecksTab();
      default:
        return renderFeatureView({
          selectedTab,
          assetKey,
          definition,
        });
    }
  };

  const reportEvents = useReportEventsModal(
    definition
      ? {
          assetKey: definition.assetKey,
          isPartitioned: definition.isPartitioned,
          repository: definition.repository,
        }
      : null,
    refreshState.refetch,
  );

  return (
    <Box
      flex={{direction: 'column', grow: 1}}
      style={{height: '100%', width: '100%', overflowY: 'auto'}}
    >
      <AssetPageHeader
        assetKey={assetKey}
        tags={
          <AssetViewPageHeaderTags
            definition={definition}
            liveData={liveDataForAsset}
            onShowUpstream={() => setParams({...params, view: 'lineage', lineageScope: 'upstream'})}
          />
        }
        tabs={
          <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-end'}}>
            <AssetTabs selectedTab={selectedTab} tabs={tabList} />
            {refreshState && (
              <Box padding={{bottom: 8}}>
                <QueryRefreshCountdown refreshState={refreshState} />
              </Box>
            )}
          </Box>
        }
        right={
          <Box style={{margin: '-4px 0'}}>
            {definition && definition.isObservable ? (
              <LaunchAssetObservationButton
                intent="primary"
                scope={{all: [definition], skipAllTerm: true}}
              />
            ) : definition && definition.jobNames.length > 0 && upstream ? (
              <LaunchAssetExecutionButton
                scope={{all: [definition]}}
                additionalDropdownOptions={reportEvents.dropdownOptions}
              />
            ) : undefined}
            {reportEvents.element}
          </Box>
        }
      />
      {!viewingMostRecent && params.asOf && (
        <HistoricalViewAlert asOf={params.asOf} hasDefinition={!!definition} />
      )}
      <ErrorBoundary region="page" resetErrorOnChange={[assetKey, params]}>
        {renderContent()}
      </ErrorBoundary>
    </Box>
  );
};

const AssetLoadingDefinitionState = () => (
  <Box
    style={{height: 390}}
    flex={{direction: 'row', justifyContent: 'center', alignItems: 'center'}}
  >
    <Spinner purpose="page" />
  </Box>
);

const AssetNoDefinitionState = () => (
  <Box padding={{vertical: 32}}>
    <NonIdealState
      title="No definition"
      description="This asset doesn't have a software definition in any of your code locations."
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

export const ASSET_VIEW_DEFINITION_QUERY = gql`
  query AssetViewDefinitionQuery($assetKey: AssetKeyInput!) {
    assetOrError(assetKey: $assetKey) {
      ... on Asset {
        id
        key {
          path
        }
        assetMaterializations(limit: 1) {
          timestamp
          runId
        }
        definition {
          id
          ...AssetViewDefinitionNode
        }
      }
    }
  }

  fragment AssetViewDefinitionNode on AssetNode {
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
    hasAssetChecks

    ...AssetNodeInstigatorsFragment
    ...AssetNodeDefinitionFragment
    ...UnderlyingOpsAssetNodeFragment
  }

  ${ASSET_NODE_INSTIGATORS_FRAGMENT}
  ${ASSET_NODE_DEFINITION_FRAGMENT}
  ${UNDERLYING_OPS_ASSET_NODE_FRAGMENT}
`;

const HistoricalViewAlert = ({asOf, hasDefinition}: {asOf: string; hasDefinition: boolean}) => {
  const {pathname, search} = useLocation();
  const searchParams = new URLSearchParams(search);
  searchParams.delete('asOf');
  searchParams.set('time', asOf);

  return (
    <Box padding={{vertical: 16, horizontal: 24}} border="bottom">
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
          <Link to={`${pathname}?${searchParams.toString()}`}>
            {hasDefinition
              ? 'Show definition and latest materializations'
              : 'Show latest materializations'}
          </Link>
        }
      />
    </Box>
  );
};

const AssetViewPageHeaderTags: React.FC<{
  definition: AssetViewDefinitionNodeFragment | null;
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
      {definition && definition.autoMaterializePolicy && <AutomaterializeDaemonStatusTag />}
      {definition && definition.freshnessPolicy && (
        <OverdueTag policy={definition.freshnessPolicy} assetKey={definition.assetKey} />
      )}
      {definition && (
        <StaleReasonsTags
          liveData={liveData}
          assetKey={definition.assetKey}
          onClick={onShowUpstream}
          include="all"
        />
      )}
      {definition && (
        <AssetComputeKindTag style={{position: 'relative'}} definition={definition} reduceColor />
      )}
    </>
  );
};
